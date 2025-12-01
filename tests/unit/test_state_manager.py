"""
Unit tests for State Manager
Tests workflow state management and checkpoints
Maps to: spec.md → FR7 (State Management)
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.lib.orchestrator.state_manager import (
    StateManager,
    WorkflowState,
    WorkflowContext,
    Checkpoint,
    CheckpointType,
    get_state_manager,
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def state_manager():
    """State manager without database (in-memory only)"""
    return StateManager(db_session=None)


@pytest.fixture
def state_manager_with_db(mock_db_session):
    """State manager with mocked database"""
    return StateManager(db_session=mock_db_session)


@pytest.mark.asyncio
class TestWorkflowCreation:
    """Test workflow creation"""
    
    async def test_create_workflow(self, state_manager):
        """Should create new workflow context"""
        # Act
        context = await state_manager.create_workflow("research")
        
        # Assert
        assert context.workflow_id is not None
        assert context.pipeline_type == "research"
        assert context.state == WorkflowState.PENDING
    
    async def test_create_workflow_with_query_id(self, state_manager):
        """Should create workflow with query ID"""
        # Act
        context = await state_manager.create_workflow("research", query_id=123)
        
        # Assert
        assert context.query_id == 123
    
    async def test_create_workflow_persists_to_db(self, state_manager_with_db, mock_db_session):
        """Should persist workflow to database"""
        # Arrange
        mock_pipeline = Mock()
        mock_pipeline.id = 1
        mock_db_session.add = Mock()
        
        # Act
        await state_manager_with_db.create_workflow("research")
        
        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called()


@pytest.mark.asyncio
class TestWorkflowStateTransitions:
    """Test workflow state transitions"""
    
    async def test_start_workflow(self, state_manager):
        """Should transition workflow to running"""
        # Arrange
        context = await state_manager.create_workflow("research")
        
        # Act
        updated = await state_manager.start_workflow(context.workflow_id)
        
        # Assert
        assert updated.state == WorkflowState.RUNNING
    
    async def test_complete_workflow(self, state_manager):
        """Should transition workflow to completed"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        updated = await state_manager.complete_workflow(context.workflow_id)
        
        # Assert
        assert updated.state == WorkflowState.COMPLETED
    
    async def test_fail_workflow(self, state_manager):
        """Should transition workflow to failed with error message"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        updated = await state_manager.fail_workflow(
            context.workflow_id,
            "Test error message"
        )
        
        # Assert
        assert updated.state == WorkflowState.FAILED
        assert updated.error_message == "Test error message"
    
    async def test_pause_workflow(self, state_manager):
        """Should transition workflow to paused"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        updated = await state_manager.pause_workflow(context.workflow_id)
        
        # Assert
        assert updated.state == WorkflowState.PAUSED
    
    async def test_resume_workflow(self, state_manager):
        """Should resume paused workflow"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        await state_manager.pause_workflow(context.workflow_id)
        
        # Act
        updated = await state_manager.resume_workflow(context.workflow_id)
        
        # Assert
        assert updated.state == WorkflowState.RUNNING
    
    async def test_resume_non_paused_workflow_fails(self, state_manager):
        """Should not resume workflow that isn't paused"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            await state_manager.resume_workflow(context.workflow_id)
        assert "cannot resume" in str(exc.value).lower()


@pytest.mark.asyncio
class TestCheckpoints:
    """Test checkpoint functionality"""
    
    async def test_add_checkpoint(self, state_manager):
        """Should add checkpoint to workflow"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        checkpoint = await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.TOPIC_CATEGORIZED,
            data={"category": "core_ai"},
        )
        
        # Assert
        assert checkpoint.checkpoint_type == CheckpointType.TOPIC_CATEGORIZED
        assert checkpoint.data["category"] == "core_ai"
        assert checkpoint.timestamp is not None
    
    async def test_multiple_checkpoints(self, state_manager):
        """Should track multiple checkpoints in order"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.TOPIC_CATEGORIZED,
        )
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.RESEARCH_STARTED,
        )
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.SOURCES_COLLECTED,
        )
        
        # Assert
        updated = await state_manager.get_context(context.workflow_id)
        assert len(updated.checkpoints) == 3
        assert updated.checkpoints[0].checkpoint_type == CheckpointType.TOPIC_CATEGORIZED
        assert updated.checkpoints[2].checkpoint_type == CheckpointType.SOURCES_COLLECTED
    
    async def test_get_last_checkpoint(self, state_manager):
        """Should return last checkpoint"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.TOPIC_CATEGORIZED,
        )
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.RESEARCH_COMPLETED,
        )
        
        # Act
        last = await state_manager.get_last_checkpoint(context.workflow_id)
        
        # Assert
        assert last.checkpoint_type == CheckpointType.RESEARCH_COMPLETED
    
    async def test_get_last_checkpoint_empty(self, state_manager):
        """Should return None if no checkpoints"""
        # Arrange
        context = await state_manager.create_workflow("research")
        
        # Act
        last = await state_manager.get_last_checkpoint(context.workflow_id)
        
        # Assert
        assert last is None
    
    async def test_checkpoint_updates_current_step(self, state_manager):
        """Should update current step when adding checkpoint"""
        # Arrange
        context = await state_manager.create_workflow("research")
        await state_manager.start_workflow(context.workflow_id)
        
        # Act
        await state_manager.add_checkpoint(
            context.workflow_id,
            CheckpointType.SOURCES_COLLECTED,
        )
        
        # Assert
        updated = await state_manager.get_context(context.workflow_id)
        assert updated.current_step == "sources_collected"


@pytest.mark.asyncio
class TestContextRetrieval:
    """Test workflow context retrieval"""
    
    async def test_get_context(self, state_manager):
        """Should retrieve workflow context"""
        # Arrange
        context = await state_manager.create_workflow("research")
        
        # Act
        retrieved = await state_manager.get_context(context.workflow_id)
        
        # Assert
        assert retrieved.workflow_id == context.workflow_id
        assert retrieved.pipeline_type == "research"
    
    async def test_get_nonexistent_context(self, state_manager):
        """Should raise error for nonexistent workflow"""
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            await state_manager.get_context(99999)
        assert "not found" in str(exc.value).lower()


class TestWorkflowContextSerialization:
    """Test context serialization"""
    
    def test_to_dict(self):
        """Should serialize context to dictionary"""
        # Arrange
        context = WorkflowContext(
            workflow_id=1,
            pipeline_type="research",
            state=WorkflowState.RUNNING,
            query_id=123,
            checkpoints=[
                Checkpoint(
                    checkpoint_type=CheckpointType.TOPIC_CATEGORIZED,
                    timestamp=datetime(2024, 1, 1, 12, 0, 0),
                    data={"category": "core_ai"},
                )
            ],
        )
        
        # Act
        data = context.to_dict()
        
        # Assert
        assert data["workflow_id"] == 1
        assert data["state"] == "running"
        assert len(data["checkpoints"]) == 1
        assert data["checkpoints"][0]["type"] == "topic_categorized"
    
    def test_from_dict(self):
        """Should deserialize context from dictionary"""
        # Arrange
        data = {
            "workflow_id": 1,
            "pipeline_type": "research",
            "state": "completed",
            "query_id": 123,
            "checkpoints": [
                {
                    "type": "research_completed",
                    "timestamp": "2024-01-01T12:00:00",
                    "data": {"completeness": 0.9},
                }
            ],
        }
        
        # Act
        context = WorkflowContext.from_dict(data)
        
        # Assert
        assert context.workflow_id == 1
        assert context.state == WorkflowState.COMPLETED
        assert len(context.checkpoints) == 1
        assert context.checkpoints[0].checkpoint_type == CheckpointType.RESEARCH_COMPLETED


class TestStateManagerFactory:
    """Test factory function"""
    
    def test_get_state_manager(self):
        """Should create state manager"""
        manager = get_state_manager()
        assert isinstance(manager, StateManager)
    
    def test_get_state_manager_with_session(self, mock_db_session):
        """Should create state manager with database session"""
        manager = get_state_manager(db_session=mock_db_session)
        assert manager.db_session == mock_db_session


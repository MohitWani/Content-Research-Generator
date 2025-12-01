"""
State Management for workflow checkpoints and recovery
Enables workflow resumption and state persistence
Maps to: spec.md → FR7 (State Management)
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.lib.models.research import PipelineExecution, ResearchQuery
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowState(str, Enum):
    """Workflow execution states"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckpointType(str, Enum):
    """Types of checkpoints in a workflow"""
    TOPIC_CATEGORIZED = "topic_categorized"
    RESEARCH_STARTED = "research_started"
    SOURCES_COLLECTED = "sources_collected"
    RESEARCH_SYNTHESIZED = "research_synthesized"
    RESEARCH_COMPLETED = "research_completed"
    BLOG_STARTED = "blog_started"
    BLOG_COMPLETED = "blog_completed"


@dataclass
class Checkpoint:
    """Represents a workflow checkpoint"""
    checkpoint_type: CheckpointType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """Context for a workflow execution"""
    workflow_id: int
    pipeline_type: str
    state: WorkflowState
    query_id: Optional[int] = None
    checkpoints: List[Checkpoint] = field(default_factory=list)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for persistence"""
        return {
            "workflow_id": self.workflow_id,
            "pipeline_type": self.pipeline_type,
            "state": self.state.value,
            "query_id": self.query_id,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "checkpoints": [
                {
                    "type": cp.checkpoint_type.value,
                    "timestamp": cp.timestamp.isoformat(),
                    "data": cp.data,
                    "metadata": cp.metadata,
                }
                for cp in self.checkpoints
            ],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """Create context from dictionary"""
        checkpoints = [
            Checkpoint(
                checkpoint_type=CheckpointType(cp["type"]),
                timestamp=datetime.fromisoformat(cp["timestamp"]),
                data=cp.get("data", {}),
                metadata=cp.get("metadata", {}),
            )
            for cp in data.get("checkpoints", [])
        ]
        
        return cls(
            workflow_id=data["workflow_id"],
            pipeline_type=data["pipeline_type"],
            state=WorkflowState(data["state"]),
            query_id=data.get("query_id"),
            checkpoints=checkpoints,
            current_step=data.get("current_step"),
            error_message=data.get("error_message"),
        )


class StateManager:
    """
    Manages workflow state and checkpoints
    Enables resumption of interrupted workflows
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize state manager
        
        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session
        self._contexts: Dict[int, WorkflowContext] = {}
        logger.info("Initialized StateManager")
    
    async def create_workflow(
        self,
        pipeline_type: str,
        query_id: Optional[int] = None,
    ) -> WorkflowContext:
        """
        Create a new workflow context
        
        Args:
            pipeline_type: Type of pipeline (research, blog_generation, etc.)
            query_id: Optional research query ID
        
        Returns:
            New WorkflowContext
        """
        # Create pipeline execution record
        if self.db_session:
            pipeline = PipelineExecution(
                pipeline_type=pipeline_type,
                research_query_id=query_id,
                status=WorkflowState.PENDING.value,
                started_at=datetime.utcnow(),
            )
            self.db_session.add(pipeline)
            await self.db_session.flush()
            workflow_id = pipeline.id
        else:
            # In-memory only
            workflow_id = len(self._contexts) + 1
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            pipeline_type=pipeline_type,
            state=WorkflowState.PENDING,
            query_id=query_id,
            started_at=datetime.utcnow(),
        )
        
        self._contexts[workflow_id] = context
        logger.debug(f"Created workflow {workflow_id} of type {pipeline_type}")
        
        return context
    
    async def start_workflow(self, workflow_id: int) -> WorkflowContext:
        """
        Mark workflow as running
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Updated WorkflowContext
        """
        context = await self.get_context(workflow_id)
        context.state = WorkflowState.RUNNING
        context.updated_at = datetime.utcnow()
        
        await self._persist_state(workflow_id, WorkflowState.RUNNING)
        
        logger.debug(f"Started workflow {workflow_id}")
        return context
    
    async def add_checkpoint(
        self,
        workflow_id: int,
        checkpoint_type: CheckpointType,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """
        Add a checkpoint to workflow
        
        Args:
            workflow_id: Workflow ID
            checkpoint_type: Type of checkpoint
            data: Checkpoint data to persist
            metadata: Additional metadata
        
        Returns:
            Created Checkpoint
        """
        context = await self.get_context(workflow_id)
        
        checkpoint = Checkpoint(
            checkpoint_type=checkpoint_type,
            timestamp=datetime.utcnow(),
            data=data or {},
            metadata=metadata or {},
        )
        
        context.checkpoints.append(checkpoint)
        context.current_step = checkpoint_type.value
        context.updated_at = datetime.utcnow()
        
        # Persist checkpoint data
        await self._persist_checkpoint(workflow_id, context)
        
        logger.debug(f"Added checkpoint {checkpoint_type.value} to workflow {workflow_id}")
        return checkpoint
    
    async def complete_workflow(
        self,
        workflow_id: int,
        final_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowContext:
        """
        Mark workflow as completed
        
        Args:
            workflow_id: Workflow ID
            final_data: Final workflow data
        
        Returns:
            Updated WorkflowContext
        """
        context = await self.get_context(workflow_id)
        context.state = WorkflowState.COMPLETED
        context.updated_at = datetime.utcnow()
        
        await self._persist_state(workflow_id, WorkflowState.COMPLETED)
        
        logger.info(f"Completed workflow {workflow_id}")
        return context
    
    async def fail_workflow(
        self,
        workflow_id: int,
        error_message: str,
    ) -> WorkflowContext:
        """
        Mark workflow as failed
        
        Args:
            workflow_id: Workflow ID
            error_message: Error description
        
        Returns:
            Updated WorkflowContext
        """
        context = await self.get_context(workflow_id)
        context.state = WorkflowState.FAILED
        context.error_message = error_message
        context.updated_at = datetime.utcnow()
        
        await self._persist_state(workflow_id, WorkflowState.FAILED, error_message)
        
        logger.error(f"Workflow {workflow_id} failed: {error_message}")
        return context
    
    async def pause_workflow(self, workflow_id: int) -> WorkflowContext:
        """
        Pause workflow for later resumption
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Updated WorkflowContext
        """
        context = await self.get_context(workflow_id)
        context.state = WorkflowState.PAUSED
        context.updated_at = datetime.utcnow()
        
        await self._persist_state(workflow_id, WorkflowState.PAUSED)
        
        logger.info(f"Paused workflow {workflow_id}")
        return context
    
    async def resume_workflow(self, workflow_id: int) -> WorkflowContext:
        """
        Resume a paused workflow
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            WorkflowContext with last checkpoint info
        """
        context = await self.get_context(workflow_id)
        
        if context.state != WorkflowState.PAUSED:
            raise ValueError(f"Cannot resume workflow in state {context.state.value}")
        
        context.state = WorkflowState.RUNNING
        context.updated_at = datetime.utcnow()
        
        await self._persist_state(workflow_id, WorkflowState.RUNNING)
        
        logger.info(
            f"Resumed workflow {workflow_id} from checkpoint: {context.current_step}"
        )
        return context
    
    async def get_context(self, workflow_id: int) -> WorkflowContext:
        """
        Get workflow context
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            WorkflowContext
        
        Raises:
            ValueError: If workflow not found
        """
        # Check in-memory cache first
        if workflow_id in self._contexts:
            return self._contexts[workflow_id]
        
        # Load from database
        if self.db_session:
            pipeline = await self.db_session.get(PipelineExecution, workflow_id)
            if pipeline:
                context = WorkflowContext(
                    workflow_id=pipeline.id,
                    pipeline_type=pipeline.pipeline_type,
                    state=WorkflowState(pipeline.status),
                    query_id=pipeline.research_query_id,
                    error_message=pipeline.error_message,
                    started_at=pipeline.started_at,
                )
                
                # Load checkpoints from execution_data
                if pipeline.execution_data and "checkpoints" in pipeline.execution_data:
                    context = WorkflowContext.from_dict({
                        **context.to_dict(),
                        "checkpoints": pipeline.execution_data["checkpoints"],
                    })
                
                self._contexts[workflow_id] = context
                return context
        
        raise ValueError(f"Workflow {workflow_id} not found")
    
    async def get_last_checkpoint(
        self,
        workflow_id: int,
    ) -> Optional[Checkpoint]:
        """
        Get the last checkpoint for a workflow
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Last Checkpoint or None
        """
        context = await self.get_context(workflow_id)
        
        if context.checkpoints:
            return context.checkpoints[-1]
        return None
    
    async def list_pending_workflows(
        self,
        pipeline_type: Optional[str] = None,
    ) -> List[WorkflowContext]:
        """
        List workflows that can be resumed
        
        Args:
            pipeline_type: Optional filter by pipeline type
        
        Returns:
            List of pending/paused WorkflowContexts
        """
        resumable = []
        
        if self.db_session:
            query = select(PipelineExecution).where(
                PipelineExecution.status.in_([
                    WorkflowState.PAUSED.value,
                    WorkflowState.RUNNING.value,  # May need recovery
                ])
            )
            
            if pipeline_type:
                query = query.where(PipelineExecution.pipeline_type == pipeline_type)
            
            result = await self.db_session.execute(query)
            pipelines = result.scalars().all()
            
            for pipeline in pipelines:
                context = await self.get_context(pipeline.id)
                resumable.append(context)
        
        return resumable
    
    # Private helper methods
    
    async def _persist_state(
        self,
        workflow_id: int,
        state: WorkflowState,
        error_message: Optional[str] = None,
    ) -> None:
        """Persist workflow state to database"""
        if not self.db_session:
            return
        
        pipeline = await self.db_session.get(PipelineExecution, workflow_id)
        if pipeline:
            pipeline.status = state.value
            if error_message:
                pipeline.error_message = error_message
            if state in [WorkflowState.COMPLETED, WorkflowState.FAILED]:
                pipeline.completed_at = datetime.utcnow()
            await self.db_session.flush()
    
    async def _persist_checkpoint(
        self,
        workflow_id: int,
        context: WorkflowContext,
    ) -> None:
        """Persist checkpoint data to database"""
        if not self.db_session:
            return
        
        pipeline = await self.db_session.get(PipelineExecution, workflow_id)
        if pipeline:
            pipeline.execution_data = context.to_dict()
            await self.db_session.flush()


def get_state_manager(db_session: Optional[AsyncSession] = None) -> StateManager:
    """Factory function to create StateManager"""
    return StateManager(db_session=db_session)


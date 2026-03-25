"""Citation management API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.output import Output
from app.models.citation import Citation, CitationType
from app.schemas.citation import (
    CitationCreate,
    CitationResponse,
    CitationWithOutputResponse,
    CitationGraphNode,
    CitationGraphResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/citations", tags=["Citations"])


@router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)
async def create_citation(
    citation_data: CitationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CitationResponse:
    """
    Create a citation from one output to another.

    Args:
        citation_data: Citation creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created citation information

    Raises:
        HTTPException: If outputs not found or user not authorized
    """
    # Verify source output exists and user owns it
    source_result = await db.execute(
        select(Output).where(Output.id == citation_data.source_output_id)
    )
    source_output = source_result.scalar_one_or_none()

    if source_output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source output not found",
        )

    if source_output.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create citations from your own outputs",
        )

    # Verify target output exists
    target_result = await db.execute(
        select(Output).where(Output.id == citation_data.target_output_id)
    )
    target_output = target_result.scalar_one_or_none()

    if target_output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target output not found",
        )

    # Check if citation already exists
    existing_result = await db.execute(
        select(Citation).where(
            Citation.source_output_id == citation_data.source_output_id,
            Citation.target_output_id == citation_data.target_output_id,
            Citation.citation_type == citation_data.citation_type,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Citation already exists",
        )

    # Create citation
    new_citation = Citation(
        source_output_id=citation_data.source_output_id,
        target_output_id=citation_data.target_output_id,
        citation_type=citation_data.citation_type,
        excerpt=citation_data.excerpt,
    )

    db.add(new_citation)
    await db.commit()
    await db.refresh(new_citation)

    return CitationResponse.model_validate(new_citation)


@router.get("/output/{output_id}/citing", response_model=list[CitationWithOutputResponse])
async def get_citing_outputs(
    output_id: str,
    citation_type: CitationType | None = Query(None, description="Filter by citation type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CitationWithOutputResponse]:
    """
    Get outputs that cite this output (incoming citations).

    Args:
        output_id: Output ID to get citations for
        citation_type: Optional filter by citation type
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of citations with source output information

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Build query for citations pointing TO this output
    query = (
        select(Citation, Output, User)
        .join(Output, Output.id == Citation.source_output_id)
        .join(User, User.id == Output.user_id)
        .where(Citation.target_output_id == output_id)
    )

    # Filter by citation type if specified
    if citation_type:
        query = query.where(Citation.citation_type == citation_type)

    # Order by creation date and paginate
    query = query.order_by(Citation.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Build response
    citations_with_outputs = []
    for citation, output, author in rows:
        citation_dict = {
            "id": citation.id,
            "source_output_id": citation.source_output_id,
            "target_output_id": citation.target_output_id,
            "citation_type": citation.citation_type,
            "excerpt": citation.excerpt,
            "created_at": citation.created_at,
            "source_output": {
                "id": output.id,
                "content": output.content[:200] + "..." if len(output.content) > 200 else output.content,
                "category": output.category,
                "created_at": output.created_at,
                "author": {
                    "id": author.id,
                    "username": author.username,
                    "display_name": author.display_name,
                    "avatar_url": author.avatar_url,
                },
            },
        }
        citations_with_outputs.append(CitationWithOutputResponse(**citation_dict))

    return citations_with_outputs


@router.get("/output/{output_id}/cited", response_model=list[CitationWithOutputResponse])
async def get_cited_outputs(
    output_id: str,
    citation_type: CitationType | None = Query(None, description="Filter by citation type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CitationWithOutputResponse]:
    """
    Get outputs cited by this output (outgoing citations).

    Args:
        output_id: Output ID to get citations for
        citation_type: Optional filter by citation type
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of citations with target output information

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Build query for citations FROM this output
    query = (
        select(Citation, Output, User)
        .join(Output, Output.id == Citation.target_output_id)
        .join(User, User.id == Output.user_id)
        .where(Citation.source_output_id == output_id)
    )

    # Filter by citation type if specified
    if citation_type:
        query = query.where(Citation.citation_type == citation_type)

    # Order by creation date and paginate
    query = query.order_by(Citation.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Build response (note: source_output here is actually the target)
    citations_with_outputs = []
    for citation, output, author in rows:
        citation_dict = {
            "id": citation.id,
            "source_output_id": citation.source_output_id,
            "target_output_id": citation.target_output_id,
            "citation_type": citation.citation_type,
            "excerpt": citation.excerpt,
            "created_at": citation.created_at,
            "source_output": {  # This is the cited output
                "id": output.id,
                "content": output.content[:200] + "..." if len(output.content) > 200 else output.content,
                "category": output.category,
                "created_at": output.created_at,
                "author": {
                    "id": author.id,
                    "username": author.username,
                    "display_name": author.display_name,
                    "avatar_url": author.avatar_url,
                },
            },
        }
        citations_with_outputs.append(CitationWithOutputResponse(**citation_dict))

    return citations_with_outputs


@router.get("/output/{output_id}/stats")
async def get_citation_stats(
    output_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get citation statistics for an output.

    Args:
        output_id: Output ID to get stats for
        db: Database session

    Returns:
        Citation statistics

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Count citations pointing TO this output (being cited)
    incoming_count = await db.scalar(
        select(func.count()).select_from(Citation).where(Citation.target_output_id == output_id)
    )

    # Count citations FROM this output (citing others)
    outgoing_count = await db.scalar(
        select(func.count()).select_from(Citation).where(Citation.source_output_id == output_id)
    )

    # Count by citation type (incoming)
    incoming_by_type = {}
    for citation_type in CitationType:
        count = await db.scalar(
            select(func.count())
            .select_from(Citation)
            .where(
                Citation.target_output_id == output_id,
                Citation.citation_type == citation_type,
            )
        )
        incoming_by_type[citation_type.value] = count or 0

    return {
        "output_id": output_id,
        "incoming_citations": incoming_count or 0,
        "outgoing_citations": outgoing_count or 0,
        "incoming_by_type": incoming_by_type,
    }


@router.get("/output/{output_id}/graph", response_model=CitationGraphResponse)
async def get_citation_graph(
    output_id: str,
    depth: int = Query(2, ge=1, le=5, description="Graph traversal depth"),
    db: AsyncSession = Depends(get_db),
) -> CitationGraphResponse:
    """
    Get citation graph for an output.

    This creates a graph showing:
    - Outputs that cite this output (incoming)
    - Outputs cited by this output (outgoing)
    - Recursively up to specified depth

    Args:
        output_id: Output ID to build graph for
        depth: How many levels to traverse
        db: Database session

    Returns:
        Citation graph data

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    root_output = output_result.scalar_one_or_none()

    if root_output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Build graph using BFS
    nodes = {}
    edges = []
    visited = set()
    queue = [(output_id, 0)]  # (output_id, current_depth)

    while queue:
        current_id, current_depth = queue.pop(0)

        if current_id in visited or current_depth > depth:
            continue

        visited.add(current_id)

        # Get output info
        output_result = await db.execute(
            select(Output, User)
            .join(User, User.id == Output.user_id)
            .where(Output.id == current_id)
        )
        row = output_result.first()

        if row:
            output, author = row
            nodes[current_id] = CitationGraphNode(
                id=output.id,
                title=output.content[:100] + "..." if len(output.content) > 100 else output.content,
                category=output.category,
                author_username=author.username,
                created_at=output.created_at,
                citation_count=0,  # Will be calculated
            )

        if current_depth < depth:
            # Get incoming citations (outputs citing this one)
            incoming_result = await db.execute(
                select(Citation).where(Citation.target_output_id == current_id)
            )
            incoming_citations = incoming_result.scalars().all()

            for citation in incoming_citations:
                edges.append({
                    "source": citation.source_output_id,
                    "target": citation.target_output_id,
                    "type": citation.citation_type.value,
                })
                queue.append((citation.source_output_id, current_depth + 1))

            # Get outgoing citations (outputs this one cites)
            outgoing_result = await db.execute(
                select(Citation).where(Citation.source_output_id == current_id)
            )
            outgoing_citations = outgoing_result.scalars().all()

            for citation in outgoing_citations:
                edges.append({
                    "source": citation.source_output_id,
                    "target": citation.target_output_id,
                    "type": citation.citation_type.value,
                })
                queue.append((citation.target_output_id, current_depth + 1))

    # Calculate citation counts for each node
    for node_id in nodes:
        count = await db.scalar(
            select(func.count())
            .select_from(Citation)
            .where(Citation.target_output_id == node_id)
        )
        nodes[node_id].citation_count = count or 0

    return CitationGraphResponse(
        root_output_id=output_id,
        nodes=list(nodes.values()),
        edges=edges,
    )


@router.delete("/{citation_id}", response_model=MessageResponse)
async def delete_citation(
    citation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Delete a citation.

    Only the owner of the source output can delete the citation.

    Args:
        citation_id: Citation ID to delete
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If citation not found or user not authorized
    """
    # Find citation
    result = await db.execute(
        select(Citation, Output)
        .join(Output, Output.id == Citation.source_output_id)
        .where(Citation.id == citation_id)
    )
    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found",
        )

    citation, source_output = row

    # Check ownership
    if source_output.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete citations from your own outputs",
        )

    # Delete citation
    await db.delete(citation)
    await db.commit()

    return MessageResponse(message="Citation deleted successfully")

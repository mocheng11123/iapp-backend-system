"""论坛和反馈 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import (
    ForumBoard, ForumPost, ForumReply, Feedback, EmailLog,
    App, Developer, EndUser
)
from app.schemas import (
    ForumBoardCreate,
    ForumBoardResponse,
    ForumPostCreate,
    ForumPostResponse,
    ForumReplyCreate,
    ForumReplyResponse,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackStatusUpdate,
    FeedbackReply,
    MessageResponse,
)
from app.services.auth import get_current_developer, api_key_auth, get_current_enduser
from datetime import datetime
from typing import Optional

router = APIRouter()


# ============ 论坛版块管理 ============

@router.post("/forum/boards", response_model=ForumBoardResponse, status_code=status.HTTP_201_CREATED)
async def create_forum_board(
    data: ForumBoardCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """创建版块"""
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    board = ForumBoard(
        app_id=app.id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    
    return ForumBoardResponse.model_validate(board)


@router.get("/forum/boards", response_model=list[ForumBoardResponse])
async def list_forum_boards(
    app_id: str = None,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """版块列表"""
    query = select(ForumBoard).join(App).where(
        App.developer_id == developer.id,
        App.is_deleted == False
    )
    
    if app_id:
        query = query.where(ForumBoard.app_id == app_id)
    
    result = await db.execute(query.order_by(ForumBoard.sort_order, ForumBoard.created_at))
    boards = result.scalars().all()
    
    return [ForumBoardResponse.model_validate(b) for b in boards]


# ============ 论坛帖子 ============

@router.post("/forum/posts", response_model=ForumPostResponse, status_code=status.HTTP_201_CREATED)
async def create_forum_post(
    data: ForumPostCreate,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """发布帖子"""
    # 检查版块是否存在
    result = await db.execute(select(ForumBoard).where(ForumBoard.id == data.board_id))
    board = result.scalar_one_or_none()
    
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    if board.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Board is closed")
    
    # 检查用户是否被封禁
    if user.status != 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")
    
    post = ForumPost(
        board_id=board.id,
        user_id=user.id,
        title=data.title,
        content=data.content,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    return ForumPostResponse.model_validate(post)


@router.get("/forum/posts", response_model=list[ForumPostResponse])
async def list_forum_posts(
    board_id: Optional[str] = Query(None),
    app_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("latest", pattern="^(latest|hot)$"),
    db: AsyncSession = Depends(get_db),
):
    """帖子列表"""
    query = select(ForumPost).join(ForumBoard).where(
        ForumBoard.app_id == app_id,
        ForumPost.status == 0
    )
    
    if board_id:
        query = query.where(ForumPost.board_id == board_id)
    
    if sort == "hot":
        query = query.order_by(ForumPost.is_sticky.desc(), ForumPost.reply_count.desc(), ForumPost.created_at.desc())
    else:
        query = query.order_by(ForumPost.is_sticky.desc(), ForumPost.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [ForumPostResponse.model_validate(p) for p in posts]


@router.get("/forum/posts/{post_id}", response_model=ForumPostResponse)
async def get_forum_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    """帖子详情"""
    result = await db.execute(select(ForumPost).where(ForumPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # 增加浏览数
    post.view_count += 1
    
    return ForumPostResponse.model_validate(post)


@router.delete("/forum/posts/{post_id}", response_model=MessageResponse)
async def delete_forum_post(
    post_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """删除帖子（开发者）"""
    result = await db.execute(
        select(ForumPost)
        .join(ForumBoard)
        .join(App)
        .where(ForumPost.id == post_id, App.developer_id == developer.id)
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    post.status = 1
    await db.commit()
    
    return MessageResponse(message="Post deleted successfully")


@router.post("/forum/posts/{post_id}/replies", response_model=ForumReplyResponse, status_code=status.HTTP_201_CREATED)
async def create_forum_reply(
    post_id: str,
    data: ForumReplyCreate,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """回复帖子"""
    result = await db.execute(select(ForumPost).where(ForumPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    reply = ForumReply(
        post_id=post.id,
        user_id=user.id,
        content=data.content,
        reply_to_id=data.reply_to_id,
    )
    db.add(reply)
    
    # 增加回复数
    post.reply_count += 1
    
    await db.commit()
    await db.refresh(reply)
    
    return ForumReplyResponse.model_validate(reply)


@router.get("/forum/posts/{post_id}/replies", response_model=list[ForumReplyResponse])
async def list_forum_replies(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取回复列表"""
    result = await db.execute(
        select(ForumReply)
        .where(ForumReply.post_id == post_id)
        .order_by(ForumReply.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    replies = result.scalars().all()
    
    return [ForumReplyResponse.model_validate(r) for r in replies]


# ============ 反馈系统 ============

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: FeedbackCreate,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """提交反馈"""
    feedback = Feedback(
        app_id=user.app_id,
        user_id=user.id,
        title=data.title,
        content=data.content,
        images=data.images,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    # TODO: 触发邮件通知 Celery 任务
    
    return FeedbackResponse.model_validate(feedback)


@router.get("/feedback", response_model=list[FeedbackResponse])
async def list_feedback(
    app_id: str = None,
    status_filter: int = Query(None, alias="status"),
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """反馈列表"""
    query = select(Feedback).join(App).where(
        App.developer_id == developer.id,
        App.is_deleted == False
    )
    
    if app_id:
        query = query.where(Feedback.app_id == app_id)
    
    if status_filter is not None:
        query = query.where(Feedback.status == status_filter)
    
    result = await db.execute(query.order_by(Feedback.created_at.desc()))
    feedbacks = result.scalars().all()
    
    return [FeedbackResponse.model_validate(f) for f in feedbacks]


@router.put("/feedback/{id}/status", response_model=MessageResponse)
async def update_feedback_status(
    id: str,
    data: FeedbackStatusUpdate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """更新反馈状态"""
    result = await db.execute(
        select(Feedback)
        .join(App)
        .where(Feedback.id == id, App.developer_id == developer.id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    
    feedback.status = data.status
    feedback.updated_at = datetime.utcnow()
    await db.commit()
    
    return MessageResponse(message="Feedback status updated")


@router.post("/feedback/{id}/reply", response_model=FeedbackResponse)
async def reply_feedback(
    id: str,
    data: FeedbackReply,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """回复反馈"""
    result = await db.execute(
        select(Feedback)
        .join(App)
        .where(Feedback.id == id, App.developer_id == developer.id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    
    feedback.reply_content = data.reply_content
    feedback.replied_at = datetime.utcnow()
    feedback.status = 2  # 已解决
    feedback.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(feedback)
    
    return FeedbackResponse.model_validate(feedback)

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.file_task import FileTask
from app.models.user import User
from app.schemas.file_task import FileTaskResponse

router = APIRouter()


async def _get_owned(db: AsyncSession, file_id: uuid.UUID, user: User) -> FileTask:
    ft = await db.get(FileTask, file_id)
    if ft is None:
        raise HTTPException(status_code=404, detail="文件任务不存在")
    if ft.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该文件")
    return ft


@router.get("", response_model=list[FileTaskResponse], summary="我的上传文件")
async def list_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await db.scalars(
        select(FileTask)
        .where(FileTask.user_id == current_user.id)
        .order_by(FileTask.created_at.desc())
    )
    return list(rows)


@router.get("/{file_id}", summary="文件任务详情")
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """含解析出的文本（parsed_content），供查看出题依据。"""
    ft = await _get_owned(db, file_id, current_user)
    return {
        **FileTaskResponse.model_validate(ft).model_dump(),
        "parsed_content": ft.parsed_content,
    }


@router.delete("/{file_id}", summary="删除文件任务")
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除记录并移除磁盘上的文件（已生成的题目保留）。"""
    ft = await _get_owned(db, file_id, current_user)
    if ft.file_path and os.path.exists(ft.file_path):
        os.remove(ft.file_path)  # ponytail: best-effort; missing file is fine
    await db.delete(ft)
    await db.commit()
    return {"detail": "已删除"}

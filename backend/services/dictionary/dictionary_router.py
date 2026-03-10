from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.dictionary import DictionaryCreate, DictionaryUpdate, DictionaryResponse
from services.dictionary.dictionary_service import DictionaryService
from config.logging import logger

router = APIRouter(
    prefix="/api/dictionaries",
    tags=["dictionary"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[DictionaryResponse])
def get_dictionaries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取字典列表"""
    logger.info(f"获取字典列表，skip: {skip}, limit: {limit}")
    dictionaries = DictionaryService.get_dictionaries(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(dictionaries)} 个字典")
    return dictionaries


@router.get("/type/{dictionary_type}", response_model=List[DictionaryResponse])
def get_dictionaries_by_type(dictionary_type: str, db: Session = Depends(get_db)):
    """根据类型获取字典列表"""
    logger.info(f"根据类型获取字典列表: {dictionary_type}")
    dictionaries = DictionaryService.get_dictionaries_by_type(db, dictionary_type=dictionary_type)
    logger.info(f"获取到 {len(dictionaries)} 个字典")
    return dictionaries


@router.get("/{dictionary_id}", response_model=DictionaryResponse)
def get_dictionary(dictionary_id: int, db: Session = Depends(get_db)):
    """根据ID获取字典"""
    logger.info(f"根据ID获取字典: {dictionary_id}")
    dictionary = DictionaryService.get_dictionary_by_id(db, dictionary_id=dictionary_id)
    if dictionary is None:
        logger.warning(f"字典未找到: {dictionary_id}")
        raise HTTPException(status_code=404, detail="Dictionary not found")
    logger.info(f"获取字典成功: {dictionary_id}")
    return dictionary


@router.post("", response_model=DictionaryResponse)
def create_dictionary(dictionary: DictionaryCreate, db: Session = Depends(get_db)):
    """创建字典"""
    logger.info(f"创建字典: {dictionary.name}")
    created_dictionary = DictionaryService.create_dictionary(db=db, dictionary=dictionary)
    logger.info(f"字典创建成功: {created_dictionary.id}")
    return created_dictionary


@router.put("/{dictionary_id}", response_model=DictionaryResponse)
def update_dictionary(dictionary_id: int, dictionary: DictionaryUpdate, db: Session = Depends(get_db)):
    """更新字典"""
    logger.info(f"更新字典: {dictionary_id}")
    db_dictionary = DictionaryService.update_dictionary(db=db, dictionary_id=dictionary_id, dictionary_update=dictionary)
    if db_dictionary is None:
        logger.warning(f"字典未找到: {dictionary_id}")
        raise HTTPException(status_code=404, detail="Dictionary not found")
    logger.info(f"字典更新成功: {dictionary_id}")
    return db_dictionary


@router.delete("/{dictionary_id}")
def delete_dictionary(dictionary_id: int, db: Session = Depends(get_db)):
    """删除字典"""
    logger.info(f"删除字典: {dictionary_id}")
    success = DictionaryService.delete_dictionary(db=db, dictionary_id=dictionary_id)
    if not success:
        logger.warning(f"字典未找到: {dictionary_id}")
        raise HTTPException(status_code=404, detail="Dictionary not found")
    logger.info(f"字典删除成功: {dictionary_id}")
    return {"message": "Dictionary deleted successfully"}

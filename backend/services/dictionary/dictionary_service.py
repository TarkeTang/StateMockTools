from typing import List, Optional
from sqlalchemy.orm import Session
from models.dictionary import Dictionary
from schemas.dictionary import DictionaryCreate, DictionaryUpdate
from config.logging import logger


class DictionaryService:
    """字典服务类"""
    
    @staticmethod
    def get_dictionaries(db: Session, skip: int = 0, limit: int = 100) -> List[Dictionary]:
        """获取字典列表"""
        logger.debug(f"获取字典列表，skip: {skip}, limit: {limit}")
        dictionaries = db.query(Dictionary).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(dictionaries)} 个字典")
        return dictionaries
    
    @staticmethod
    def get_dictionary_by_id(db: Session, dictionary_id: int) -> Optional[Dictionary]:
        """根据ID获取字典"""
        logger.debug(f"根据ID获取字典: {dictionary_id}")
        dictionary = db.query(Dictionary).filter(Dictionary.id == dictionary_id).first()
        logger.debug(f"获取字典结果: {'成功' if dictionary else '失败'}")
        return dictionary
    
    @staticmethod
    def get_dictionaries_by_type(db: Session, dictionary_type: str) -> List[Dictionary]:
        """根据类型获取字典列表"""
        logger.debug(f"根据类型获取字典列表: {dictionary_type}")
        dictionaries = db.query(Dictionary).filter(Dictionary.type == dictionary_type).all()
        logger.debug(f"获取到 {len(dictionaries)} 个字典")
        return dictionaries
    
    @staticmethod
    def create_dictionary(db: Session, dictionary: DictionaryCreate) -> Dictionary:
        """创建字典"""
        logger.debug(f"创建字典: {dictionary.name}")
        db_dictionary = Dictionary(**dictionary.model_dump())
        db.add(db_dictionary)
        db.commit()
        db.refresh(db_dictionary)
        logger.debug(f"字典创建成功: {db_dictionary.id}")
        return db_dictionary
    
    @staticmethod
    def update_dictionary(db: Session, dictionary_id: int, dictionary_update: DictionaryUpdate) -> Optional[Dictionary]:
        """更新字典"""
        logger.debug(f"更新字典: {dictionary_id}")
        db_dictionary = db.query(Dictionary).filter(Dictionary.id == dictionary_id).first()
        if db_dictionary:
            update_data = dictionary_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_dictionary, field, value)
            db.commit()
            db.refresh(db_dictionary)
            logger.debug(f"字典更新成功: {dictionary_id}")
        else:
            logger.debug(f"字典未找到: {dictionary_id}")
        return db_dictionary
    
    @staticmethod
    def delete_dictionary(db: Session, dictionary_id: int) -> bool:
        """删除字典"""
        logger.debug(f"删除字典: {dictionary_id}")
        db_dictionary = db.query(Dictionary).filter(Dictionary.id == dictionary_id).first()
        if db_dictionary:
            db.delete(db_dictionary)
            db.commit()
            logger.debug(f"字典删除成功: {dictionary_id}")
            return True
        logger.debug(f"字典未找到: {dictionary_id}")
        return False

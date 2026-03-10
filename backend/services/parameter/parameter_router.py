from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.parameter import (
    ParameterCreate, ParameterUpdate, ParameterResponse,
    ParameterTestRequest, ParameterTestResponse
)
from services.parameter.parameter_service import ParameterService
from config.logging import logger

router = APIRouter(
    prefix="/api/parameters",
    tags=["parameter"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[ParameterResponse])
def get_parameters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取参数列表"""
    logger.info(f"获取参数列表，skip: {skip}, limit: {limit}")
    parameters = ParameterService.get_parameters(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(parameters)} 个参数")
    return parameters


@router.get("/enabled", response_model=List[ParameterResponse])
def get_enabled_parameters(db: Session = Depends(get_db)):
    """获取所有启用的参数"""
    logger.info("获取启用的参数")
    parameters = ParameterService.get_enabled_parameters(db)
    logger.info(f"获取到 {len(parameters)} 个启用的参数")
    return parameters


@router.get("/{parameter_id}", response_model=ParameterResponse)
def get_parameter(parameter_id: int, db: Session = Depends(get_db)):
    """根据 ID 获取参数"""
    logger.info(f"根据 ID 获取参数：{parameter_id}")
    parameter = ParameterService.get_parameter_by_id(db, parameter_id=parameter_id)
    if parameter is None:
        logger.warning(f"参数未找到：{parameter_id}")
        raise HTTPException(status_code=404, detail="Parameter not found")
    logger.info(f"获取参数成功：{parameter_id}")
    return parameter


@router.post("", response_model=ParameterResponse)
def create_parameter(parameter: ParameterCreate, db: Session = Depends(get_db)):
    """创建参数"""
    logger.info(f"创建参数请求：{parameter.model_dump()}")
    
    # 验证参数名称格式
    if not parameter.name.startswith('${') or not parameter.name.endswith('}'):
        raise HTTPException(status_code=400, detail="参数名称必须以 ${ 开头，以 } 结尾，如：${timestamp}")
    
    created_parameter = ParameterService.create_parameter(db=db, parameter=parameter)
    logger.info(f"参数创建成功：{created_parameter.id}")
    return created_parameter


@router.put("/{parameter_id}", response_model=ParameterResponse)
def update_parameter(parameter_id: int, parameter: ParameterUpdate, db: Session = Depends(get_db)):
    """更新参数"""
    logger.info(f"更新参数请求：parameter_id={parameter_id}, data={parameter.model_dump(exclude_unset=True)}")
    db_parameter = ParameterService.update_parameter(db=db, parameter_id=parameter_id, parameter_update=parameter)
    if db_parameter is None:
        logger.warning(f"参数未找到：{parameter_id}")
        raise HTTPException(status_code=404, detail="Parameter not found")
    logger.info(f"参数更新成功：{parameter_id}")
    return db_parameter


@router.delete("/{parameter_id}")
def delete_parameter(parameter_id: int, db: Session = Depends(get_db)):
    """删除参数"""
    logger.info(f"删除参数：{parameter_id}")
    success = ParameterService.delete_parameter(db=db, parameter_id=parameter_id)
    if not success:
        logger.warning(f"参数未找到：{parameter_id}")
        raise HTTPException(status_code=404, detail="Parameter not found")
    logger.info(f"参数删除成功：{parameter_id}")
    return {"message": "Parameter deleted successfully"}


@router.post("/test", response_model=ParameterTestResponse)
def test_parameter_replacement(request: ParameterTestRequest, db: Session = Depends(get_db)):
    """测试参数替换"""
    logger.info(f"测试参数替换：{request.content}")
    
    try:
        replaced, parameters = ParameterService.test_parameter_replacement(request.content, db)
        logger.info(f"替换结果：{replaced}")
        
        return ParameterTestResponse(
            original=request.content,
            replaced=replaced,
            parameters=[{'name': p.name, 'type': p.param_type, 'value': p.value} for p in parameters]
        )
    except Exception as e:
        logger.error(f"参数替换失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"参数替换失败：{str(e)}")

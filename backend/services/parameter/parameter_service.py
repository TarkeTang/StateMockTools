from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from models.parameter import Parameter
from schemas.parameter import ParameterCreate, ParameterUpdate
from config.logging import logger
import re
import random
import string
from datetime import datetime


class ParameterService:
    """参数服务类"""

    @staticmethod
    def get_parameters(db: Session, skip: int = 0, limit: int = 100) -> List[Parameter]:
        """获取参数列表"""
        logger.debug(f"获取参数列表，skip: {skip}, limit: {limit}")
        parameters = db.query(Parameter).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(parameters)} 个参数")
        return parameters

    @staticmethod
    def get_parameter_by_id(db: Session, parameter_id: int) -> Optional[Parameter]:
        """根据 ID 获取参数"""
        logger.debug(f"根据 ID 获取参数：{parameter_id}")
        parameter = db.query(Parameter).filter(Parameter.id == parameter_id).first()
        logger.debug(f"获取参数结果：{'成功' if parameter else '失败'}")
        return parameter

    @staticmethod
    def get_enabled_parameters(db: Session) -> List[Parameter]:
        """获取所有启用的参数"""
        logger.debug("获取启用的参数")
        parameters = db.query(Parameter).filter(Parameter.enabled == True).all()
        logger.debug(f"获取到 {len(parameters)} 个启用的参数")
        return parameters

    @staticmethod
    def create_parameter(db: Session, parameter: ParameterCreate) -> Parameter:
        """创建参数"""
        logger.debug(f"创建参数：{parameter.name}")
        db_parameter = Parameter(**parameter.model_dump())
        db.add(db_parameter)
        db.commit()
        db.refresh(db_parameter)
        logger.debug(f"参数创建成功：{db_parameter.id}")
        return db_parameter

    @staticmethod
    def update_parameter(db: Session, parameter_id: int, parameter_update: ParameterUpdate) -> Optional[Parameter]:
        """更新参数"""
        logger.debug(f"更新参数：{parameter_id}")
        db_parameter = db.query(Parameter).filter(Parameter.id == parameter_id).first()
        if db_parameter:
            update_data = parameter_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_parameter, field, value)
            db.commit()
            db.refresh(db_parameter)
            logger.debug(f"参数更新成功：{parameter_id}")
        else:
            logger.debug(f"参数未找到：{parameter_id}")
        return db_parameter

    @staticmethod
    def delete_parameter(db: Session, parameter_id: int) -> bool:
        """删除参数"""
        logger.debug(f"删除参数：{parameter_id}")
        db_parameter = db.query(Parameter).filter(Parameter.id == parameter_id).first()
        if db_parameter:
            db.delete(db_parameter)
            db.commit()
            logger.debug(f"参数删除成功：{parameter_id}")
            return True
        logger.debug(f"参数未找到：{parameter_id}")
        return False

    @staticmethod
    def replace_parameters(content: str, parameters: List[Parameter]) -> str:
        """
        替换消息内容中的参数
        支持参数格式：${parameter_name}
        
        参数类型：
        - timestamp: 时间戳（毫秒/秒）
        - datetime: 日期时间（支持格式：yyyy-MM-dd HH:mm:ss）
        - custom: 自定义固定值
        - random: 随机值（支持范围：random[1-100] 或 random[abc,def,ghi]）
        """
        result = content
        used_params = []

        for param in parameters:
            if not param.enabled:
                continue

            param_pattern = re.escape(param.name)
            match = re.search(param_pattern, result)
            if not match:
                continue

            replace_value = ParameterService._generate_param_value(param)
            if replace_value:
                result = re.sub(param_pattern, replace_value, result)
                used_params.append({
                    'name': param.name,
                    'type': param.param_type,
                    'value': replace_value
                })
                logger.debug(f"参数替换：{param.name} -> {replace_value}")

        return result

    @staticmethod
    def _generate_param_value(param: Parameter) -> str:
        """生成参数值"""
        param_type = param.param_type.lower()

        if param_type == 'timestamp':
            # 时间戳（毫秒）
            return str(int(datetime.now().timestamp() * 1000))

        elif param_type == 'timestamp_s':
            # 时间戳（秒）
            return str(int(datetime.now().timestamp()))

        elif param_type == 'datetime':
            # 日期时间
            fmt = param.format or '%Y-%m-%d %H:%M:%S'
            # 支持 Java 风格格式转换
            fmt = ParameterService._convert_java_format(fmt)
            return datetime.now().strftime(fmt)

        elif param_type == 'custom':
            # 自定义固定值
            return param.value or ''

        elif param_type == 'random':
            # 随机值
            value = param.value or '1-100'
            return ParameterService._generate_random(value)

        elif param_type == 'uuid':
            # UUID
            import uuid
            return str(uuid.uuid4())

        return param.value or ''

    @staticmethod
    def _convert_java_format(fmt: str) -> str:
        """转换 Java 日期格式为 Python 格式"""
        conversions = {
            'yyyy': '%Y',
            'yy': '%y',
            'MM': '%m',
            'dd': '%d',
            'HH': '%H',
            'hh': '%I',
            'mm': '%M',
            'ss': '%S',
            'SSS': '%f',
            'a': '%p',
        }
        result = fmt
        for java_fmt, python_fmt in conversions.items():
            result = result.replace(java_fmt, python_fmt)
        return result

    @staticmethod
    def _generate_random(value: str) -> str:
        """生成随机值"""
        # 数字范围：random[1-100]
        range_match = re.match(r'(\d+)-(\d+)', value)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            return str(random.randint(start, end))

        # 列表随机：random[a,b,c]
        if ',' in value:
            items = [item.strip() for item in value.split(',')]
            return random.choice(items)

        # 默认随机字符串
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    @staticmethod
    def test_parameter_replacement(content: str, db: Session) -> tuple:
        """测试参数替换"""
        parameters = ParameterService.get_enabled_parameters(db)
        replaced = ParameterService.replace_parameters(content, parameters)
        return replaced, parameters

    @staticmethod
    def replace_parameters_with_db(content: str, db: Session) -> str:
        """从数据库获取参数并替换"""
        parameters = ParameterService.get_enabled_parameters(db)
        return ParameterService.replace_parameters(content, parameters)

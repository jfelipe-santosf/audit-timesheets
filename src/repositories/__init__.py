from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List
from src.models import Employee, TimeRecord, Shift


class EmployeeRepository(ABC):
    """Interface para repositório de funcionários"""
    
    @abstractmethod
    def get_active_employees(self) -> List[Employee]:
        pass
    
    @abstractmethod
    def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        pass
    
    @abstractmethod
    def save_employee(self, employee: Employee) -> None:
        pass


class TimeRecordRepository(ABC):
    """Interface para repositório de registros de ponto"""
    
    @abstractmethod
    def get_records_by_employee_and_period(
        self, 
        employee_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[TimeRecord]:
        pass
    
    @abstractmethod
    def get_records_by_shift_and_date(
        self,
        shift_id: int,
        record_date: date
    ) -> List[TimeRecord]:
        pass
    
    @abstractmethod
    def save_record(self, record: TimeRecord) -> None:
        pass
    
    @abstractmethod
    def update_record(self, record: TimeRecord) -> None:
        pass


class ShiftRepository(ABC):
    """Interface para repositório de turnos"""
    
    @abstractmethod
    def get_shift_by_id(self, shift_id: int) -> Optional[Shift]:
        pass
    
    @abstractmethod
    def get_all_shifts(self) -> List[Shift]:
        pass
    
    @abstractmethod
    def save_shift(self, shift: Shift) -> None:
        pass

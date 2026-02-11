from src.repositories import EmployeeRepository, TimeRecordRepository, ShiftRepository
from src.models import Employee, TimeRecord, Shift, ShiftTolerance
from datetime import datetime, date, time
from typing import List, Optional


class InMemoryEmployeeRepository(EmployeeRepository):
    """Implementação em memória do repositório de funcionários"""
    
    def __init__(self):
        self.employees = {}
    
    def add_employee(self, employee: Employee):
        self.employees[employee.id] = employee
    
    def get_active_employees(self) -> List[Employee]:
        return [e for e in self.employees.values() if e.active]
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        return self.employees.get(employee_id)
    
    def save_employee(self, employee: Employee) -> None:
        self.employees[employee.id] = employee


class InMemoryTimeRecordRepository(TimeRecordRepository):
    """Implementação em memória do repositório de registros de ponto"""
    
    def __init__(self):
        self.records = {}
        self.next_id = 1
    
    def add_record(self, record: TimeRecord):
        if record.id == 0:
            record.id = self.next_id
            self.next_id += 1
        self.records[record.id] = record
    
    def get_records_by_employee_and_period(
        self, 
        employee_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[TimeRecord]:
        return [
            r for r in self.records.values()
            if r.employee_id == employee_id 
            and start_date <= r.record_date <= end_date
        ]
    
    def get_records_by_shift_and_date(
        self,
        shift_id: int,
        record_date: date
    ) -> List[TimeRecord]:
        return [
            r for r in self.records.values()
            if r.shift_id == shift_id and r.record_date == record_date
        ]
    
    def save_record(self, record: TimeRecord) -> None:
        if record.id == 0:
            record.id = self.next_id
            self.next_id += 1
        self.records[record.id] = record
    
    def update_record(self, record: TimeRecord) -> None:
        self.records[record.id] = record
    
    def get_all_records(self) -> List[TimeRecord]:
        return list(self.records.values())


class InMemoryShiftRepository(ShiftRepository):
    """Implementação em memória do repositório de turnos"""
    
    def __init__(self):
        self.shifts = {}
    
    def add_shift(self, shift: Shift):
        self.shifts[shift.id] = shift
    
    def get_shift_by_id(self, shift_id: int) -> Optional[Shift]:
        return self.shifts.get(shift_id)
    
    def get_all_shifts(self) -> List[Shift]:
        return list(self.shifts.values())
    
    def save_shift(self, shift: Shift) -> None:
        self.shifts[shift.id] = shift

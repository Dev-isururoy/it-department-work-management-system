from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_max_length=20000)
class Login(Strict):
    username: str = Field(min_length=1,max_length=80)
    password: str = Field(min_length=1,max_length=200)
    setup_key: str = ''
class UserEdit(Strict):
    name: str = Field(min_length=1,max_length=100)
    username: str = Field(min_length=1,max_length=80,pattern=r'^[a-z0-9._-]+$')
    role: Literal['manager','member']='member'
    active: bool = True
    password: str = Field(default='',max_length=200)
class TaskCreate(Strict):
    title: str = Field(min_length=1,max_length=200)
    description: str = ''
    category: str = 'Uncategorized'
    department: str = ''
    location: str = ''
    equipment_id: str = ''
    owner: int
    supporters: list[int] = Field(default_factory=list,max_length=50)
    priority: Literal['Low','Normal','High','Critical']='Normal'
    due: str = ''
    work_date: str = ''
    checklist: list[str] = Field(default_factory=list,max_length=100)
    required_evidence: str = ''
    review_required: bool = True
    vendor_id: str = ''
    purchase_id: str = ''
    project_id: str = ''
    parent_id: str = ''
    related_id: str = ''
    impact: str = ''
    complexity: Literal['Small','Medium','Large']='Medium'
class Change(Strict):
    version: int
    action: str
    reason: str = ''
    data: dict = Field(default_factory=dict)
class Progress(Strict):
    note: str = ''
    status: Literal['Open','Assigned','In Progress','Waiting'] | None = None
    blocker: str | None = None
    completion_summary: str | None = None
    test_results: str | None = None
    checked: list[str] | None = None
    start_time: str | None = None
    finish_time: str | None = None
    effort_minutes: float | None = Field(default=None,ge=0,le=1000000)
    work_date: str | None = None
class Record(Strict):
    data: dict
    version: int | None = None
    reason: str = ''
class Schedule(Strict):
    title: str = Field(min_length=1,max_length=200)
    owner: int
    frequency: Literal['daily','weekly','monthly','weekdays']
    start: str
    due_time: str = '17:00'
    due_at_period_end: bool = False
    weekdays: list[int] = Field(default_factory=list)
    month_day: int = Field(default=1,ge=1,le=31)
    paused: bool = False
    responsibility_id: str = ''
    description: str = ''
    category: str = 'Routine check'
    required_evidence: str = ''
    review_required: bool = True

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.schemas.precommit import FileChange
from src.services.validator import ValidationEngine
from src.services.rule_store import RuleStore

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///data/compliance.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    file = FileChange(file_path="test.py", content="DEBUG = True\nverify=False\nbypass_governance = True\nenable_guardrails = False\n")
    
    async with async_session() as db:
        rules = await RuleStore.list_rules(db, active_only=True)
        print(f"Loaded {len(rules)} rules")
        validator = ValidationEngine()
        findings = await validator.validate([file], db)
        print("FINDINGS:")
        for f in findings:
            print("-", f.message)

asyncio.run(test())

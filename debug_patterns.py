import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.schemas.precommit import FileChange
from src.services.validator import ValidationEngine
from src.services.rule_store import RuleStore
import re

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///data/compliance.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        rules = await RuleStore.list_rules(db, active_only=True)
        for r in rules:
            if "bypass" in str(r["regex_patterns"]):
                 print("Rule title:", r["rule_title"])
                 for p in r["regex_patterns"]:
                     print(f"Testing pattern (raw string repr): {repr(p)}")
                     compiled = re.compile(p, re.IGNORECASE)
                     print(f"Match against 'bypass_governance = True':", bool(compiled.search("bypass_governance = True")))

asyncio.run(test())

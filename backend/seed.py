"""Database seed script — creates demo organizations, users, and work items.

Run with: python -m seed
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, engine, Base
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.work_item import LeadWorkItem, WorkItemStatus
from app.models.audit_log import AuditLog, AuditAction
from app.models.background_job import BackgroundJob
from app.core.security import hash_password
from app.services.llm_service import MockLLMProvider


# Seed data
ORGANIZATIONS = [
    {"name": "Acme Corp"},
    {"name": "TechFlow Inc"},
]

LEADS = [
    {
        "lead_name": "Sarah Chen",
        "company_name": "DataVault Solutions",
        "lead_context": "VP of Engineering at DataVault Solutions. They recently raised a $15M Series A and are expanding their cloud infrastructure team. Currently evaluating sales automation platforms to scale their outbound efforts. Previously used HubSpot but looking for more AI-native tooling.",
        "original_input": "Attended our webinar on 'AI-Driven Sales Operations' and downloaded the enterprise whitepaper. Asked specific questions about API integrations and data security during the Q&A.",
    },
    {
        "lead_name": "Marcus Johnson",
        "company_name": "GreenScale Energy",
        "lead_context": "Director of Business Development at GreenScale Energy, a fast-growing renewable energy startup. They have 50+ sales reps and are struggling with inconsistent follow-up quality. Looking to standardize their outreach process.",
        "original_input": "Connected on LinkedIn after commenting on our post about sales AI. Mentioned they're 'drowning in leads but not converting enough.' Asked for a demo.",
    },
    {
        "lead_name": "Priya Patel",
        "company_name": "FinEdge Analytics",
        "lead_context": "CRO at FinEdge Analytics, a fintech company with 200 employees. They're implementing a new CRM system and want to integrate AI-powered sales workflows. Budget approved for Q2.",
        "original_input": "Inbound request through our website contact form. Said: 'We need to 3x our pipeline without 3x-ing our team. How can your AI help?'",
    },
    {
        "lead_name": "James Morrison",
        "company_name": "CloudBridge Systems",
        "lead_context": "Head of Sales Operations at CloudBridge Systems. Enterprise B2B SaaS company selling to Fortune 500. They have a complex sales cycle of 6-9 months and want AI to help with mid-funnel nurturing.",
        "original_input": "Referred by an existing customer (TechNova). Looking specifically at AI follow-up generation and approval workflows for their sales team of 30.",
    },
    {
        "lead_name": "Emily Rodriguez",
        "company_name": "MedConnect Health",
        "lead_context": "VP of Growth at MedConnect Health, a healthcare SaaS platform. They sell to hospital networks and need compliant, personalized outreach. Current pain point is their sales team spends 40% of time writing emails.",
        "original_input": "Met at SaaStr Annual conference. Expressed strong interest in AI-assisted email drafting with human approval workflow. Wants to ensure HIPAA-friendly communications.",
    },
    {
        "lead_name": "David Kim",
        "company_name": "UrbanFlow Logistics",
        "lead_context": "CEO of UrbanFlow Logistics, a Series B logistics tech company. They're scaling from 100 to 500 enterprise customers this year and need to automate their sales process. Currently doing everything manually.",
        "original_input": "Filled out our ROI calculator and showed potential 45% efficiency gain. Followed up by requesting a personalized demo for his team.",
    },
    {
        "lead_name": "Lisa Thompson",
        "company_name": "EduSpark Learning",
        "lead_context": "Director of Partnerships at EduSpark Learning, an edtech company. They partner with school districts and need to follow up with procurement officers efficiently. Seasonal sales cycle with Q3 being critical.",
        "original_input": "Downloaded our case study on 'AI in Education Sales.' Left a note saying: 'We lose deals because we can't follow up fast enough during the procurement window.'",
    },
    {
        "lead_name": "Robert Chang",
        "company_name": "SecureNet Cyber",
        "lead_context": "SVP of Sales at SecureNet Cyber, a cybersecurity firm. They deal with highly technical buyers and need AI that can generate contextually accurate, technical follow-ups. Team of 80 sales reps across 3 regions.",
        "original_input": "Attended our product demo and asked detailed questions about prompt customization, data privacy, and SOC 2 compliance. Requested a security review document.",
    },
    {
        "lead_name": "Amanda Foster",
        "company_name": "BrightPath Consulting",
        "lead_context": "Managing Partner at BrightPath Consulting, a management consulting firm. They want to use AI to help their consultants with business development follow-ups. Currently losing 30% of warm leads due to slow responses.",
        "original_input": "Cold outreach response. Said: 'We've been looking at tools like this. Can you show me how it handles nuanced, relationship-driven sales conversations?'",
    },
    {
        "lead_name": "Carlos Mendez",
        "company_name": "AgriTech Innovations",
        "lead_context": "Head of Sales at AgriTech Innovations, an agricultural technology company. They sell to farmers and agricultural cooperatives across Latin America. Need multilingual follow-up capabilities.",
        "original_input": "Inbound from Google search for 'AI sales assistant B2B.' Specifically interested in multilingual support and CRM integration with Salesforce.",
    },
]


async def seed_database():
    """Create demo data in the database."""
    llm = MockLLMProvider()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        try:
            # Create organizations
            orgs = []
            for org_data in ORGANIZATIONS:
                org = Organization(name=org_data["name"])
                db.add(org)
                orgs.append(org)
            await db.flush()

            print(f"✓ Created {len(orgs)} organizations")

            # Create users for each org
            users = {}
            for org in orgs:
                admin = User(
                    organization_id=org.id,
                    name=f"Admin User",
                    email=f"admin@{org.name.lower().replace(' ', '')}.com",
                    role=UserRole.ADMIN,
                    password_hash=hash_password("admin123"),
                )
                reviewer = User(
                    organization_id=org.id,
                    name=f"Reviewer User",
                    email=f"reviewer@{org.name.lower().replace(' ', '')}.com",
                    role=UserRole.REVIEWER,
                    password_hash=hash_password("reviewer123"),
                )
                db.add(admin)
                db.add(reviewer)
                users[org.id] = {"admin": admin, "reviewer": reviewer}
            await db.flush()

            print(f"✓ Created {len(users) * 2} users")

            # Create work items for the first organization (Acme Corp)
            acme_org = orgs[0]
            acme_reviewer = users[acme_org.id]["reviewer"]

            work_items = []
            for i, lead in enumerate(LEADS):
                # Generate AI draft
                ai_draft = await llm.generate_follow_up(
                    lead_name=lead["lead_name"],
                    company_name=lead["company_name"],
                    lead_context=lead["lead_context"],
                    original_input=lead["original_input"],
                )

                # Vary statuses for realistic demo
                status = WorkItemStatus.PENDING_REVIEW
                if i == 3:
                    status = WorkItemStatus.SENT
                elif i == 5:
                    status = WorkItemStatus.REJECTED
                elif i == 7:
                    status = WorkItemStatus.FAILED

                item = LeadWorkItem(
                    organization_id=acme_org.id,
                    assigned_reviewer_id=acme_reviewer.id,
                    lead_name=lead["lead_name"],
                    company_name=lead["company_name"],
                    lead_context=lead["lead_context"],
                    original_input=lead["original_input"],
                    ai_output=ai_draft,
                    status=status,
                    created_at=datetime.now(timezone.utc) - timedelta(hours=i * 2),
                )
                db.add(item)
                work_items.append(item)
            await db.flush()

            print(f"✓ Created {len(work_items)} work items for Acme Corp")

            # Create some work items for TechFlow too
            techflow_org = orgs[1]
            techflow_reviewer = users[techflow_org.id]["reviewer"]

            for lead in LEADS[:4]:
                ai_draft = await llm.generate_follow_up(
                    lead_name=lead["lead_name"],
                    company_name=lead["company_name"],
                    lead_context=lead["lead_context"],
                    original_input=lead["original_input"],
                )
                item = LeadWorkItem(
                    organization_id=techflow_org.id,
                    assigned_reviewer_id=techflow_reviewer.id,
                    lead_name=lead["lead_name"],
                    company_name=lead["company_name"],
                    lead_context=lead["lead_context"],
                    original_input=lead["original_input"],
                    ai_output=ai_draft,
                    status=WorkItemStatus.PENDING_REVIEW,
                )
                db.add(item)
            await db.flush()

            print(f"✓ Created 4 work items for TechFlow Inc")

            # Create audit logs for the work items
            for item in work_items:
                db.add(AuditLog(
                    organization_id=acme_org.id,
                    work_item_id=item.id,
                    action=AuditAction.ITEM_CREATED,
                    metadata_json={
                        "lead_name": item.lead_name,
                        "company_name": item.company_name,
                    },
                ))
                db.add(AuditLog(
                    organization_id=acme_org.id,
                    work_item_id=item.id,
                    action=AuditAction.AI_DRAFT_GENERATED,
                    metadata_json={"draft_length": len(item.ai_output)},
                ))

            await db.commit()
            print(f"✓ Created audit log entries")

            print("\n" + "=" * 50)
            print("🎉 Seed data created successfully!")
            print("=" * 50)
            print("\nTest Credentials:")
            print(f"\n  Acme Corp (Org 1):")
            print(f"    Admin:    admin@acmecorp.com / admin123")
            print(f"    Reviewer: reviewer@acmecorp.com / reviewer123")
            print(f"\n  TechFlow Inc (Org 2):")
            print(f"    Admin:    admin@techflowinc.com / admin123")
            print(f"    Reviewer: reviewer@techflowinc.com / reviewer123")
            print()

        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())

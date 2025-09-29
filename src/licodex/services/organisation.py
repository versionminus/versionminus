from sqlalchemy.ext.asyncio import AsyncSession
from licodex.repositories.organisation import (
    get_by_name,
    get_by_id,
    create as repo_create,
    list_all,
    list_with_counts,
)
from licodex.models.organisation import Organisation

class OrganisationNotFoundError(Exception):
    pass

class DuplicateOrganisationNameError(Exception):
    pass

async def create_organisation(session: AsyncSession, name: str) -> Organisation:
    existing = await get_by_name(session, name)
    if existing:
        raise DuplicateOrganisationNameError()
    return await repo_create(session, name)

async def get_organisation_or_404(session: AsyncSession, org_id) -> Organisation:  # type: ignore
    org = await get_by_id(session, org_id)
    if not org:
        raise OrganisationNotFoundError()
    return org

async def list_organisations(session: AsyncSession) -> list[Organisation]:
    return await list_all(session)

async def list_organisations_with_counts(session: AsyncSession) -> list[tuple[Organisation, int]]:
    return await list_with_counts(session)

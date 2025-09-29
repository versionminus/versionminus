from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from licodex.api import deps
from licodex.schemas.organisation import OrganisationCreate, OrganisationRead, OrganisationWithCount
from licodex.services.organisation import (
    create_organisation,
    list_organisations,
    list_organisations_with_counts,
    DuplicateOrganisationNameError,
)

router = APIRouter(prefix="/organisations", tags=["organisations"],
                   responses={404: {"description": "Not found"}},
                   )

@router.post("/", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED,
             summary="Create an organisation",
             description="Create a new organisation with a unique name.")
async def create_organisation_route(payload: OrganisationCreate, session: AsyncSession = Depends(deps.get_db)):
    try:
        org = await create_organisation(session, payload.name)
        await session.commit()
        return org
    except DuplicateOrganisationNameError:
        raise HTTPException(status_code=409, detail="Organisation name already exists")

@router.get("/", response_model=list[OrganisationRead], summary="List organisations",
            description="Return all organisations ordered by creation timestamp.")
async def list_organisations_route(session: AsyncSession = Depends(deps.get_db)):
    return await list_organisations(session)

@router.get("/with-counts", response_model=list[OrganisationWithCount], summary="List organisations with user counts",
            description="Return all organisations along with the number of users assigned to each.")
async def list_organisations_with_counts_route(session: AsyncSession = Depends(deps.get_db)):
    rows = await list_organisations_with_counts(session)
    # map to schema objects manually
    items = []
    for org, count in rows:
        items.append(OrganisationWithCount(id=org.id, name=org.name, created_at=org.created_at, user_count=count))
    return items

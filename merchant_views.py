# from contextlib import asynccontextmanager

# import aiohttp
# from redis.asyncio import Redis
# from fastapi import Depends, FastAPI, Request
# from sqlalchemy.ext.asyncio import AsyncSession

# from auth.clients import MerchantApiClient
# from auth.dao import SimplePasswordAuthDAO
# from auth.dto import AuthCredentials, UserPrivate
# from auth.services.merchant_oauth_service import MerchantOAuthPasswordAuthService
# from database import get_db

# merchant_app = FastAPI(prefix="/merchant", tags=["merchant"])


# async def get_merchant_client(request: Request):
#     return MerchantApiClient(session=request.state.session)


# async def get_redis():
#     return aioredis.Redis()


# async def get_merchant_dao(
#     session: AsyncSession = Depends(get_db),
# ):
#     return SimplePasswordAuthDAO(session=session)


# async def get_merchant_auth_service(
#     session: AsyncSession = Depends(get_db),
#     merchant_dao: SimplePasswordAuthDAO = Depends(get_merchant_dao),
#     merchantClient: MerchantApiClient = Depends(get_merchant_client),
#     redis: aioredis.Redis = Depends(get_redis),
# ):
#     return MerchantOAuthPasswordAuthService(
#         session=session,
#         auth_dao=merchant_dao,
#         merchant_client=merchantClient,
#         redis=redis,
#     )


# @merchant_app.get("/signin")
# async def authenticate_merchant(
#     auth_info: AuthCredentials,
#     merchant_service: MerchantOAuthPasswordAuthService = Depends(
#         get_merchant_auth_service
#     ),
# ):
#     token_info = merchant_service.login_for_access_token(auth_info, role=["merchant"])
#     return token_info


# @merchant_app.get("/signup")
# async def register_merchant(
#     registration_info: UserPrivate,
#     merchant_service: MerchantOAuthPasswordAuthService = Depends(
#         get_merchant_auth_service
#     ),
# ):
#     auth_model = merchant_service.create_user(registration_info)
#     return auth_model


# # @merchant_app.on_event("startup")
# # async def startup_event(request: Request):
# #     async with aiohttp.ClientSession() as session:
# #         request.state.session = session


# # @merchant_app.on_event("shutdown")
# # async def shutdown_event(request: Request):
# #     await request.state.session.close()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     async with aiohttp.ClientSession() as sess:
#         app.state.session = sess

#     yield

#     await app.state.session.close()

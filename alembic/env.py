# from logging.config import fileConfig
# import os
# from sqlalchemy import create_engine
# from sqlalchemy import pool
# import alembic.context as alembic_context

# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
# config = alembic_context.config

# # Interpret the config file for Python logging.
# fileConfig(config.config_file_name)

# # add your model's MetaData object here
# # from myapp import mymodel
# # target_metadata = mymodel.Base.metadata

# # other values from the config, defined by the needs of env.py,
# # can be acquired:
# # my_important_option = config.get_main_option("my_important_option")


# def run_migrations_offline():
#     url = config.get_main_option("sqlalchemy.url")
#     alembic_context.configure(url=url, literal_binds=True)

#     with alembic_context.begin_transaction():
#         alembic_context.run_migrations()


# def run_migrations_online():
#     connectable = create_engine(config.get_main_option("sqlalchemy.url"))

#     with connectable.connect() as connection:
#         alembic_context.configure(connection=connection)

#         with alembic_context.begin_transaction():
#             alembic_context.run_migrations()


# if alembic_context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()

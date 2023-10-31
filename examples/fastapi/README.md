# FastAPI + SQLModel + SQLAlchemy-file + Azure Blob Storage Examples

This is an example application using FastAPI, SQLModel, SQLAlchemy-File, and Azure Blob Storage. Follow
these steps to run the example locally:

## Prerequisites

Before you begin, make sure you have the following prerequisites installed:

- [Git](https://git-scm.com/)
- [Python 3](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/) (for running the Azurite storage emulator)

## Installation and Setup

1. Clone the repository to your local machine:

```shell
git clone https://github.com/jowilf/sqlalchemy-file.git
cd sqlalchemy-file
```

2. Create and activate a virtual environment:

```shell
python3 -m venv env
source env/bin/activate
```

3. Install the required Python packages:

```shell
pip install -r 'examples/fastapi/requirements.txt'
```

4. Run the [Azurite storage emulator](https://github.com/Azure/Azurite)

This step assumes you have Docker installed.

```shell
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite azurite-blob --blobHost 0.0.0.0
```

5. Start the FastAPI application:

```shell
uvicorn examples.fastapi.app:app --reload
```

6. Open your web browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). You can now interact
   with the application through the Swagger documentation. Create a new category, explore the API, and test its
   functionality.

<img width="1432" alt="Screenshot 2023-10-31 at 5 50 57 PM" src="https://github.com/jowilf/sqlalchemy-file/assets/31705179/fadd400e-c744-4ba9-a69b-8a0e731e7875">

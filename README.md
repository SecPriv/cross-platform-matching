# Cross-Platform App Matching

This repository contains the code from the 2024 MSR Paper "Comparing Apples to Androids: Discovery, Retrieval, and Matching of iOS and Android Apps for Cross-Platform Analyses" by Magdalena Steinböck, Jakob Bleier, Mikka Rainer, Tobias Urban, Christine Utz, and Martina Lindorfer. 

We're currently documenting our analysis pipeline and setup. Soon we will publish the code to:
    - scrape store information
    - download apps
    - extract features for matching

Additionally, we make available:
    - the full list of matches produced for our paper
    - the full list of reference pairs we collected

If you use this work in whole or in part for academic purposes please cite:

>Steinböck, M., Bleier, J., Rainer, M., Urban, T., Utz, C., & Lindorfer, M. (2024). Comparing Apples to Androids: Discovery, Retrieval, and Matching of iOS and Android Apps for Cross-Platform Analyses. Proceedings of the 21st International Conference on Mining Software Repositories (MSR). https://doi.org/10.1145/3643991.3644896

## Table of Contents

- [Datasets](#datasets)
- [Usage](#usage)
    1. [System Requirements](#1-system-requirements)
    2. [Python Package Dependencies](#2-python-package-dependencies)
    3. [Start Database](#3-start-database)
    4. [Executing the Python Scripts](#4-executing-the-python-scripts)
- [Development](#development)
- [License](#license)

## Datasets

For our 2024 MSR paper we also provide two datasets:

1. First the reference pairs we scraped from the Google migration API. You can find them in `data/reference-pairs.csv.zip`, which contains a zipped csv with header that describes the columns.
2. The list of best matches we computed. They are in `data/computed-matches.json` and represent, for each iOS bundle id, the highest scoring Android app after cross-compiling the top 10k apps from each store.
3. The list of best matches that we could verify using the Google migration API. They are in `data/computed-matches-verified.json`.



## Usage

### 0. Clone the repo

If not done already, you need to clone this repo. This is done via the `git` terminal command:

```sh
git clone git@github.com:SecPriv/cross-platform-matching.git
```

If you don't have git installed, please install it. You can visit https://git-scm.com/ or search for instructions online.

After you have clone the repo, go into the the directoy:

```sh
cd cross-platform-matching
```

The folder `cross-platform-matching` is considered the _project root_.

### 1. System Requirements

You need to have the following installed on your system:
- [Docker](https://www.docker.com/) (tested with 24.0.5)
- [Python](https://www.python.org/) (tested with 3.11.8)

If you don't know how to install them, please search for instructions on your own, as we can't provide guidance for every OS + architecture.

OS wise, the code has been executed on Linux x86 and Apple M1 ARM. 32GB of RAM or more are recommended, especially during matching of thousands of apps.

### 2. Python Package Dependencies

We provide dependency information for both `poetry` and `pip`.

#### pip (easy)

We highly recommend first creating a [virtual env](https://docs.python.org/3/library/venv.html) before installing any dependencies. Otherwise all packages will be installed globally and may cause conflicts with other projects that you might need to run.

<details>
    <summary>Create a virtual env</summary>

To create a virtual env, simply run this from the project root:

```sh
python -m venv venv
```

This will create a `venv` folder where all the dependencies will be installed to. However, in order to configure python properly, you must activate it first.

| OS | Command |
|---:|:------|
| Unix (Linux/MacOS) | `source ./venv/bin/activate` |
| Windows Powershell | `.\venv\Scripts\Activate.ps1` |
| Windows CMD | `.\venv\Scripts\activate.bat` |

> [!WARNING]  
> You need to active the Python virtual env every time you spawn a new shell! Otherwise python will only use and update the *globally* installed packages! 
>
> Most IDEs have good support for python virtual env, however. Please research on your own, how to build a workflow that suits your needs.

</details>

We provide a `requirements.txt` in the project root. You can install all listed dependencies by running:

```sh
# Don't forget to activate the virtual env first!
python -m pip install -r requirements.txt
```

#### poetry (reproducible)

Poetry works similarly to `venv`, but provides better stability of dependencies. If you have not already installed it, follow the [official documentation](https://python-poetry.org/docs/).

When poetry is installed, you can simply run:

```sh
poetry install
```

### 3. Start Database

**Option 1: Run locally**

We are using Docker to run the database. To simplify the setup, we are providing a [`docker-compose.yml`](./docker-compose.yml) file.

To start the database, run the following command from a terminal in the project root.

```sh
# use the -d flag to run database in the background
docker compose up -d
```

> [!NOTE] 
> Older versions of Docker may not provide the `docker compose` sub-command. If the command fails, try the old `docker-compose` command instead.

When the command finished, the database should be available shortly after on port `27017`(the default port of MongoDB). The default credentials are `localadmin` for both username and password.

**Option 2: Connect to a remote instance (e.g. sharing an instance between runners)**

If you need to connect to a remote MongoDB instance, you must set the `MONGO_URL` env variable to something like this:

```sh
MONGO_URL="mongodb://<username>:<password>@<domain or IP>:<port>/"
```

To change the name of the DB to use, set the `MONGO_DB` env variable.

```sh
MONGO_DB="name-of-your-db"
```

If setting an env variable is not possible or feasible for you, you can also update the [`db_connector.py`](code/database/db_connector.py) file.

> [!CAUTION]
> Never ever commit credentials to a git repository!    
> Git is not a secure storage for confidential information.


#### MongoDB GUI

For viewing and querying data, we recommend [MongoDB Compass](https://www.mongodb.com/products/tools/compass). It's a free GUI tool provided by MongoDB.

### 4. Executing the Python Scripts

All python scripts are executed from within the [`./code`](./code/) folder. Otherwise imports cannot be resolved.

```sh
cd code
```

The pipeline is split into multiple steps that have different requirements:

#### 1. Scraping metadata from stores

#### 2. Filtering / Selecting apps to download

#### 3. Downloading apps

##### for iOS

##### for Android

### 4. Preprocessing features

### 5. Computing scores

> Usage:
> ```sh
> python -m app_matcher.threaded_matcher --help
> ```

There are three required parameters:
- `--ios-collection`: Name of the collection (or view) where the iOS analysis results reside. 
- `--android-collection`: Name of the collection (or view) where the Android analysis results reside.
- `--matches-collection`: Name of the collection, where the results are written to.

> [!WARNING]  
> The `--matches-collection` is **not** cleared before running. So if there is an error during execution, you must manually clear the collection or choose a different name. Otherwise you will have duplicate entires in the `--matches-collection`!

## Development

## License

The Cross-Platform App Matching code is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

# Troubleshooting

<details>
    <summary>Cannot start the database due to a port conflict</summary>

This can happen, if the default port of MongoDB (`27017`) is already in use. You can change the port of MongoDB in the `docker-compose.yml`

```yml
# ...
    ports:
        - "127.0.0.1:<change this port>:27017"
#....
```

Note, however, that you also need to update the connection string.

This can either be done, by setting the `MONGO_URL` env variable to something like this:

```
mongodb://localadmin:localadmin@localhost:<your changed port>/
```

or by updating the default value in the [`db_connector.py`](code/database/db_connector.py) file.

> [!CAUTION]
> Never ever commit credentials to a git repository!    
> Git is not a secure storage for confidential information.

</details>

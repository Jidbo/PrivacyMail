<div align="center">
    <br><br>
    <img src="privacymail/website/src/assets/images/logo.png" width="10%">
    <br>
    <h1>PrivacyMail</h1><br>
</div>

PrivacyMail is an E-mail privacy analysis system. For more information about the platform, visit
[privacymail.info](https://privacymail.info).

## Installation

PrivacyMail is a Django-based website and uses `docker-compose` to run in production. To run PrivacyMail, copy
the `docker-compose.yml.example` and adjust the environment variables to your prefered settings. Before you run
start you need to clone the repository and initilize all git submodules with
`git submodule update --init --recursive`. Then you can build the cointainers with `docker-compose build`. To
start Privacymail run `docker-compose up`.

## Development

If you want to do some local development, you can either use your own postgres database or you can use the `db`
docker container. The database connection (and every other setting) can be done in an `.env` file that needs to
be placed in `privacymail/privacymail`. You can just copy the
[privacymail/privacymail/env.example](privacymail/privacymail/env.example) and change it to your needs.

After cloning the repository you have to setup OpenWPM. Please refer to the
[OpenWPM Repository](https://github.com/mozilla/OpenWPM).

You also need to setup the conda environment. To create the conda environment run
`conda env create --file=environment.yaml` from the root directory of the repository. After doing that activate
the conda environment with `conda activate privacymail`.

To actually start the development server, make sure your conda environment is activated and then run
`python manage.py runserver` from the [privacymail](privacymail/) directory. This starts the django backend.
To start the frontend, `cd` to [privacymail/website](privacymail/website) and run `npm run start`.

If your database is running, you should now be able to access you local instance of privacymail at
[https://localhost:3000/](https://localhost:3000).

## License

PrivacyMail is licensed under the GPLv3 license. See the license [here](LICENSE.txt).

## Citation

If you use PrivacyMail in a scientific project, please cite our paper at the Annual Privacy Forum 2019:

```
@article{PrivacyMail,
    title = {{Towards Transparency in Email Tracking}},
    author = {Maass, Max and Schwär, Stephan and Hollick, Matthias},
    journal = {Annual Privacy Forum},
    year = {2019}
}
```

## Acknowledgement
The creation of PrivacyMail was funded in part by the DFG as part of project C.1 within the [RTG 2050 "Privacy and Trust for Mobile Users"](https://www.informatik.tu-darmstadt.de/privacy-trust/privacy_and_trust/index.en.jsp).

#### Installing server through Docker:
- To run the code successfully, you need the following:
	- Download the model and the moral-foundation dict from [here](https://drive.google.com/drive/folders/1ytIG3S4FFEDMCLFR23iLcv11HbrhhHuF?usp=sharing) into `moral_debater_code/moral_debater/resources`
	- Create a `config.ini` file under `moral_debater_code/moral_debater/resources/` that contains the following:
	```
		[DATAPATHS]
		moral_classifier_path=/app/moral_debater_code/moral_debater/resources/moral_classifier
		emfd_moral_wordlist=/app/moral_debater_code/moral_debater/resources/eMFD_wordlist.csv
		cache_path=/app/moral_debater_code/moral_debater/resources/fetched_arguments.json

		[KEYS]
		ibm_api_key=<Project Debater API key>
	```
	Project Debater API key can be obtained from \href[here]{https://early-access-program.debater.res.ibm.com/}

	- Finally, run `docker build .`. This command will create a docker container and run the server under localhost:8080
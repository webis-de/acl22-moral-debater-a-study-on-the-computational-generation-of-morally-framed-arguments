To run the code using FLASK:

**Install torch:** 
pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html

in the directory code, run the command: pip install -r requirements.txt

In the config.ini file, which is located in code/moral_debater/resources, change the paths and add key.

Then, on terminal type the following commands:

export FLASK_APP=application.py
export FLASK_ENV=development
flask run --host=0.0.0.0


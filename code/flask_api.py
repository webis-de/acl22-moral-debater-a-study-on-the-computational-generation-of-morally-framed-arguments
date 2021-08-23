from config import App

if __name__ == '__main__':
   print(App.config().get(section='DATAPATHS', option='moral_dict_path'))
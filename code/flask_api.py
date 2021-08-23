from config import App

if __name__ == '__main__':
   print(App.config().get(section='data_paths', option='moral_dict_path'))
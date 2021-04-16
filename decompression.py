import os
import zipfile
from zipfile import BadZipfile
if __name__ == "__main__":
    # base="./"
    # pros=os.listdir(base)
    # for pro in pros:
    #     cmprs_dir=base+pro+'/dep'
    #     # print(cmprs_dir)
    #     if os.path.exists(cmprs_dir):
    #         for root, ds, fs in os.walk(cmprs_dir):
    #             for f in fs:
    #                 portion=f.split('-')
    #                 if portion[-1]=="sources.jar":
    #                     try:
    #                         print("before",os.path.join(root,f))
    #                         zip_file = zipfile.ZipFile(os.path.join(root,f))
    #                         unzip_dir=os.path.join(root,os.path.splitext(f)[0])
    #                         if not os.path.exists(unzip_dir):
    #                             print("after",unzip_dir)
    #                             zip_file.extractall(unzip_dir)
    #                     except BadZipfile:
    #                         continue
    cmprs_dir="./repository"
    for root, ds, fs in os.walk(cmprs_dir):
        for f in fs:
            portion = f.split('-')
            if portion[-1] == "sources.jar":
                try:
                    print("before", os.path.join(root, f))
                    zip_file = zipfile.ZipFile(os.path.join(root, f))
                    unzip_dir = os.path.join(root, os.path.splitext(f)[0])
                    if not os.path.exists(unzip_dir):
                        print("after", unzip_dir)
                        zip_file.extractall(unzip_dir)
                except BadZipfile:
                    continue
    # for root, ds, fs in os.walk(cmprs_dir):
    #     for f in fs:
    #         portion = os.path.splitext(f)
    #         try:
    #             if portion[-1] == ".jar":
    #                 print("before", os.path.join(root, f))
    #                 zip_file = zipfile.ZipFile(os.path.join(root, f))
    #                 unzip_dir = os.path.join(root, portion[0])
    #                 print("after", unzip_dir)
    #                 zip_file.extractall(unzip_dir)
    #         except FileNotFoundError as e:
    #             continue




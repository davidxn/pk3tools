import os
import os.path
import shutil
import zipfile
import sys

class FileHandler:
        
    LIBRARY_FOLDER = 'pk3toolslib'
    
    @classmethod
    def createFolder(cls, folderName):
        try:
            os.makedirs(folderName)
            return True
        except:
            return False
    
    @classmethod
    def fileExists(cls, fileName):
        return os.path.exists(fileName)
        
    @classmethod
    def deleteFile(cls, fileName):
        if (os.path.isdir(fileName)):
            shutil.rmtree(fileName)
        if (os.path.isfile(fileName)):
            os.remove(fileName)
        
    @classmethod
    def copyFolder(cls, source, destination):
        if (cls.fileExists(source)):
            shutil.copytree(source, destination)
    
    @classmethod
    def copyFile(cls, source, destination):
        shutil.copy(source, destination)
        
    @classmethod
    def concatenateFiles(cls, sources, destination, header = ""):
        with open(destination,'wb') as wfd:
            wfd.write(header.encode())
            for f in sources:
                with open(f,'rb') as fd:
                    wfd.write(("// ---- " + f + "\n\n").encode())
                    shutil.copyfileobj(fd, wfd)
                    wfd.write(b"\n\n")

    @classmethod
    def zipProject(cls, projectName):
        trueProjectName = projectName[projectName.rfind(os.path.sep)+1:]
        ziptarget = os.path.join(projectName, trueProjectName + ".pk3")
        foldertozip = os.path.join(projectName, "pk3")
        zipobj = zipfile.ZipFile(ziptarget, 'w', zipfile.ZIP_DEFLATED)
        rootlen = len(foldertozip) + 1
        print ("Writing " + ziptarget);
        for base, dirs, files in os.walk(foldertozip):
            for file in files:
                fn = os.path.join(base, file)
                if (fn.lower().startswith(os.path.join(projectName.lower(), "pk3", "maps")) and not fn.lower().endswith(".wad")):
                    continue
                print(fn)
                zipobj.write(fn, fn[rootlen:])

    @classmethod
    def zipPackage(cls, packageName):            
        ziptarget = os.path.join(cls.LIBRARY_FOLDER, packageName + ".pk3t")
        foldertozip = os.path.join(cls.LIBRARY_FOLDER, packageName)
        zipobj = zipfile.ZipFile(ziptarget, 'w', zipfile.ZIP_DEFLATED)
        rootlen = len(foldertozip) + 1
        for base, dirs, files in os.walk(foldertozip):
            for file in files:
                fn = os.path.join(base, file)
                print(fn)
                zipobj.write(fn, fn[rootlen:])

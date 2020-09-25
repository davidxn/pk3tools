from filehandler import FileHandler
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import json
import os
import sys

class PackageHandler:
        
    LIBRARY_FOLDER = 'pk3toolslib'
    PACKAGE_DOWNLOAD_PREFIX = 'http://doom.teamouse.net/pk3tools/lib/'
    PACKAGE_FILE_EXTENSION = 'pk3t'
    PACKAGE_DESCRIPTION_FILE = 'pk3t.json'
    PROJECT_DESCRIPTION_FILE = 'pk3tproject.json'

    @classmethod
    def createLibrary(cls):
        FileHandler.createFolder(cls.LIBRARY_FOLDER)
    
    @classmethod
    def updatePackage(cls, packageName):
        cls.createLibrary()
        print ("- Attempting to download package '" + packageName + "'")
        url = cls.PACKAGE_DOWNLOAD_PREFIX + "/" + packageName + "." + cls.PACKAGE_FILE_EXTENSION
        try:
            response = urllib.request.urlopen(url)
        except urllib.error.HTTPError as exception:
            print ("X Failed to download package '" + packageName + "' : " + str(exception))
            return False
        print ("- Downloaded package '" + packageName + "'")
        zipbytes = BytesIO(response.read())
        zipfile = ZipFile(zipbytes)
        zipfile.extractall(cls.LIBRARY_FOLDER + "/" + packageName)
        return True
    
    @classmethod
    def verifyPackage(cls, packageName):
        if (FileHandler.fileExists(cls.LIBRARY_FOLDER + "/" + packageName)):
            print ("- Package '" + packageName + "' found in library")
            return True
        return cls.updatePackage(packageName)
    
    @classmethod
    def addPackageToProject(cls, packageName, projectName):
        projectDescription = cls.getProjectDescription(projectName)
        installedPackages = projectDescription.get('installed', [])
        newlyInstalledPackages = []
        print("Packages in project '" + projectName + "' : " + str(installedPackages))
        
        if (packageName in installedPackages):
            print ("- Package '" + packageName + "' already installed in project '" + projectName + "'")
            return
            
        packagesNeeded = [packageName]
        packageListIndex = 0
        while (True):
            if (packageListIndex >= len(packagesNeeded)):
                break
            currentPackage = packagesNeeded[packageListIndex]
            if (currentPackage not in installedPackages):
                if (not cls.verifyPackage(currentPackage)):
                    print ("X Could not find or download package '" + currentPackage + "'")
                    return
                # OK, we need this one. Get its dependencies
                print ("- Getting dependencies for '" + currentPackage + "'")
                desc = cls.getPackageDescription(currentPackage)
                dependencies = desc.get('needs', [])
                for dependencyName in dependencies:
                    print ("-- Requires package '" + dependencyName + "'")
                    if (dependencyName not in packagesNeeded):
                        packagesNeeded.append(dependencyName)
            packageListIndex = packageListIndex + 1

        packagesNeeded.reverse()
        
        print ("- Installing required packages!")
        for packageNeeded in packagesNeeded:                
            if (packageNeeded in installedPackages):
                print ("- Package '" + packageNeeded + "' already installed in project '" + projectName + "'")
            else:
                cls.installPackage(packageNeeded, projectName)
                newlyInstalledPackages.append(packageNeeded)

        # We've installed successfully! Add everything to the project description file
        installedPackages = installedPackages + newlyInstalledPackages
        cls.saveProjectDescription(projectName, {'installed': installedPackages})
        cls.generateTextFiles(projectName)
            
    @classmethod
    def removePackageFromProject(cls, packageName, projectName):
        print ("- Uninstalling '" + packageName + "' from project '" + projectName + "'")

        projectDescription = cls.getProjectDescription(projectName)
        installedPackages = projectDescription.get('installed', [])

        if (packageName not in installedPackages):
            print ("- Package '" + packageName + "' not installed in project '" + projectName + "'")
            return

        FileHandler.deleteFile(os.path.join(projectName, "pk3", "sounds", packageName))
        FileHandler.deleteFile(os.path.join(projectName, "pk3", "sprites", packageName))
        FileHandler.deleteFile(os.path.join(projectName, "pk3", "decorate." + packageName))
        FileHandler.deleteFile(os.path.join(projectName, "pk3", "zscript." + packageName))
        
        installedPackages.remove(packageName)
        cls.saveProjectDescription(projectName, {'installed': installedPackages})
        cls.generateTextFiles(projectName)
        
        print ("- Uninstalled")
    
    @classmethod
    def installPackage(cls, packageName, projectName):

        print ("- Installing '" + packageName + "' to project '" + projectName + "'")

        packageFolder = cls.LIBRARY_FOLDER + "/" + packageName
        if (FileHandler.fileExists(packageFolder + "/sndinfo.txt")):
            print ("-- Installing sounds for '" + packageName + "'")
            FileHandler.copyFolder(packageFolder + "/sounds", projectName + "/pk3/sounds/" + packageName)

        if (FileHandler.fileExists(packageFolder + "/decorate.txt")):
            print ("-- Installing DECORATE for '" + packageName + "'")
            FileHandler.copyFile(packageFolder + "/decorate.txt", projectName + "/pk3/decorate." + packageName)

        if (FileHandler.fileExists(packageFolder + "/zscript.txt")):
            print ("-- Installing ZSCRIPT for '" + packageName + "'")
            FileHandler.copyFile(packageFolder + "/zscript.txt", projectName + "/pk3/zscript." + packageName)

        if (FileHandler.fileExists(packageFolder + "/gldefs.txt")):
            print ("-- Installing GLDEFS for '" + packageName + "'")
            FileHandler.copyFolder(packageFolder + "/BM", projectName + "/pk3/BM/" + packageName)

        if (FileHandler.fileExists(packageFolder + "/sprites")):
            print ("-- Installing sprites for '" + packageName + "'")
            FileHandler.copyFolder(packageFolder + "/sprites", projectName + "/pk3/sprites/" + packageName)

        print ("- Installed '" + packageName + "'")
    
    @classmethod
    def getPackageDescription(cls, packageName):
        data = json.load(open(cls.LIBRARY_FOLDER + "/" + packageName + "/" + cls.PACKAGE_DESCRIPTION_FILE))
        return data
        
    @classmethod
    def getProjectDescription(cls, projectName):
        data = json.load(open(projectName + "/" + cls.PROJECT_DESCRIPTION_FILE))
        return data
    
    @classmethod
    def saveProjectDescription(cls, projectName, data):
        with open(projectName + "/" + cls.PROJECT_DESCRIPTION_FILE, 'w') as outfile:
            json.dump(data, outfile)
        print ("- Saved " + projectName + " description file")
        
    @classmethod
    def generateMapinfo(cls, projectName):
        print ("Updating MAPINFO.pk3t")
        output = cls.getAutoGenerateWarning("MAPINFO")
        output = output + "DoomEdNums {\n"
        projectDescription = cls.getProjectDescription(projectName)
        installedPackages = projectDescription.get('installed', [])
        for installedPackage in installedPackages:
            cls.verifyPackage(installedPackage)
            desc = cls.getPackageDescription(installedPackage)
            doomednums = desc.get("doomednums", {})
            for doomednum, classname in doomednums.items():
                output = output + "    " + doomednum + " = " + classname + "\n"
        output = output + "}\n"
        with open(projectName + "/pk3/mapinfo.pk3t", 'w') as file:
            file.write(output)
    
    @classmethod
    def generateSndinfo(cls, projectName):
        print ("Updating SNDINFO.pk3t")
        projectDescription = cls.getProjectDescription(projectName)
        installedPackages = projectDescription.get('installed', [])
        filesToConcatenate = []
        for installedPackage in installedPackages:
            cls.verifyPackage(installedPackage)
            sndinfofilename = os.path.join(cls.LIBRARY_FOLDER, installedPackage, "sndinfo.txt")
            if FileHandler.fileExists(sndinfofilename):
                filesToConcatenate.append(sndinfofilename)
        FileHandler.concatenateFiles(filesToConcatenate, os.path.join(projectName, "pk3", "sndinfo.pk3t"), cls.getAutoGenerateWarning("SNDINFO"))

    @classmethod
    def generateGldefs(cls, projectName):
        print ("Updating GLDEFS.pk3t")
        projectDescription = cls.getProjectDescription(projectName)
        installedPackages = projectDescription.get('installed', [])
        filesToConcatenate = []
        for installedPackage in installedPackages:
            cls.verifyPackage(installedPackage)
            sndinfofilename = os.path.join(cls.LIBRARY_FOLDER, installedPackage, "gldefs.txt")
            if FileHandler.fileExists(sndinfofilename):
                filesToConcatenate.append(sndinfofilename)
        FileHandler.concatenateFiles(filesToConcatenate, os.path.join(projectName, "pk3", "gldefs.pk3t"), cls.getAutoGenerateWarning("GLDEFS"))
        
    @classmethod
    def getAutoGenerateWarning(cls, filetype):
        return ("/////////////////////////////////////////////////////////////\n"
        + "// " + filetype + " generated by PK3Tools!\n"
        + "// Don't modify things here as they'll be overwritten.\n"
        + "// Create your own lump and use it alongside this one instead\n"
        + "/////////////////////////////////////////////////////////////\n\n")
        
    @classmethod
    def buildProject(cls, projectName):
        cls.generateTextFiles(projectName)
        print ("Zipping project '" + projectName + "'!")
        FileHandler.zipProject(projectName)
        print ("Project '" + projectName + "' built successfully")

    @classmethod
    def generateTextFiles(cls, projectName):
        cls.generateMapinfo(projectName)
        cls.generateSndinfo(projectName)
        cls.generateGldefs(projectName)

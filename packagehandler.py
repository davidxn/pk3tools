from filehandler import FileHandler
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import json
import os
import sys

class PackageHandler:
        
    LIBRARY_FOLDER = 'pk3toolslib'
    REPOSITORY_PREFIX = 'http://doom.teamouse.net/pk3tools/'
    PACKAGE_FILE_EXTENSION = 'pk3t'
    PACKAGE_DESCRIPTION_FILE = 'pk3t.json'
    PROJECT_DESCRIPTION_FILE = 'pk3tproject.json'
    
    def __init__(self, projectPath):
        self.projectPath = projectPath

    def createLibrary(self):
        FileHandler.createFolder(self.LIBRARY_FOLDER)
    
    def downloadPackage(self, packageName):
        self.createLibrary()
        print ("- Attempting to download package '" + packageName + "'")
        url = self.REPOSITORY_PREFIX + "/lib/" + packageName + "." + self.PACKAGE_FILE_EXTENSION
        try:
            response = urllib.request.urlopen(url)
        except urllib.error.HTTPError as exception:
            print ("X Failed to download package '" + packageName + "' : " + str(exception))
            return False
        print ("- Downloaded package '" + packageName + "'")
        zipbytes = BytesIO(response.read())
        zipfile = ZipFile(zipbytes)
        zipfile.extractall(self.LIBRARY_FOLDER + "/" + packageName)
        return True

    def verifyPackage(self, packageName):
        if (FileHandler.fileExists(self.LIBRARY_FOLDER + "/" + packageName)):
            print ("- Package '" + packageName + "' found in library")
            return True
        return self.downloadPackage(packageName)
    
    def installPackageTree(self, packageName):
        projectDescription = self.getProjectDescription()
        installedPackages = projectDescription.get('installed', [])
        newlyInstalledPackages = []
        print("Packages in project '" + self.projectPath + "' : " + str(installedPackages))
        
        if (packageName in installedPackages):
            print ("- Package '" + packageName + "' already installed in project '" + self.projectPath + "'")
            return
            
        packagesNeeded = [packageName]
        packageListIndex = 0
        while (True):
            if (packageListIndex >= len(packagesNeeded)):
                break
            currentPackage = packagesNeeded[packageListIndex]
            if (currentPackage not in installedPackages):
                if (not self.verifyPackage(currentPackage)):
                    print ("X Could not find or download package '" + currentPackage + "'")
                    return
                # OK, we need this one. Get its dependencies
                print ("- Getting dependencies for '" + currentPackage + "'")
                desc = self.getPackageDescription(currentPackage)
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
                print ("- Package '" + packageNeeded + "' already installed in project '" + self.projectPath + "'")
            else:
                self.__installPackage(packageNeeded)
                newlyInstalledPackages.append(packageNeeded)

        # We've installed successfully! Add everything to the project description file
        installedPackages = installedPackages + newlyInstalledPackages
        self.saveProjectDescription({'installed': installedPackages})
        self.generateMapinfo()
            
    #TODO Needs to be rewritten to account for new way of installing
    def removePackageFromProject(self, packageName):
        print ("- Uninstalling '" + packageName + "' from project '" + self.projectPath + "'")

        projectDescription = self.getProjectDescription()
        installedPackages = projectDescription.get('installed', [])

        if (packageName not in installedPackages):
            print ("- Package '" + packageName + "' not installed in project '" + self.projectPath + "'")
            return
            
        self.deleteIncludeFileSegment("decorate", packageName)
        self.deleteIncludeFileSegment("zscript", packageName)
        self.deleteIncludeFileSegment("sndinfo", packageName)
        self.deleteIncludeFileSegment("gldefs", packageName)
        self.deleteIncludeFileSegment("credits", packageName)

        FileHandler.deleteFile(os.path.join(self.projectPath, "pk3", "sounds", "pk3t", packageName))
        FileHandler.deleteFile(os.path.join(self.projectPath, "pk3", "sprites", "pk3t", packageName))
        FileHandler.deleteFile(os.path.join(self.projectPath, "pk3", "decorate", "pk3t", packageName))
        FileHandler.deleteFile(os.path.join(self.projectPath, "pk3", "zscript", "pk3t", packageName))
        FileHandler.deleteFile(os.path.join(self.projectPath, "pk3", "BM", "pk3t", packageName))
        
        installedPackages.remove(packageName)
        self.saveProjectDescription({'installed': installedPackages})
        self.generateMapinfo()
        print ("- Uninstalled")

    ## Performs the internals of copying a package's files to a project and updating the project's include files
    def __installPackage(self, packageName):

        print ("- Installing '" + packageName + "' to project '" + self.projectPath + "'")

        packageFolder = self.LIBRARY_FOLDER + "/" + packageName
        if (FileHandler.fileExists(packageFolder + "/sndinfo.txt")):
            self.__installNonIncludableScript("sndinfo", packageName)
        if (FileHandler.fileExists(packageFolder + "/gldefs.txt")):
            print ("-- Installing GLDEFS for '" + packageName + "'")
            self.__installNonIncludableScript("gldefs", packageName)
        if (FileHandler.fileExists(packageFolder + "/credits.txt")):
            print ("-- Installing credits for '" + packageName + "'")
            self.__installNonIncludableScript("credits", packageName)

        if (FileHandler.fileExists(packageFolder + "/decorate.txt")):
            self.__installIncludableScript("decorate", packageName)
        if (FileHandler.fileExists(packageFolder + "/zscript.txt")):
            self.__installIncludableScript("zscript", packageName)

        if (FileHandler.fileExists(packageFolder + "/sprites")):
            print ("-- Installing sprites for '" + packageName + "'")
            FileHandler.copyFolder(packageFolder + "/sprites", self.getDataFolderForPackage("sprites", packageName))
        print ("- Installed '" + packageName + "'")
        
    def __installNonIncludableScript(self, scriptType, packageName):
            print ("-- Installing " + scriptType + " for '" + packageName + "'")
            packageFolder = self.LIBRARY_FOLDER + "/" + packageName
            
            folderToCopy = ""
            if (scriptType == "sndinfo"):
                folderToCopy = "sounds"
            if (scriptType == "gldefs"):
                folderToCopy = "BM"
            
            if (folderToCopy):
                FileHandler.copyFolder(packageFolder + "/" + folderToCopy, self.getDataFolderForPackage(folderToCopy, packageName))
            with open(packageFolder + "/" + scriptType + ".txt") as file:
                fileString = file.read()
            self.updateIncludeFileSegment(scriptType, packageName, fileString)

    def __installIncludableScript(self, scriptType, packageName):
        packageFolder = self.LIBRARY_FOLDER + "/" + packageName
        ## If there's a folder for this script, copy it all in and then use the contents of the package's txt in our include file
        if (FileHandler.fileExists(packageFolder + "/" + scriptType)):
            print ("-- Installing " + scriptType + " folder for '" + packageName + "'")
            destinationFolder = self.getDataFolderForPackage(scriptType, packageName)
            FileHandler.copyFolder(packageFolder + "/" + scriptType + "/", destinationFolder)
            fileString = ""
            with open(packageFolder + "/" + scriptType + ".txt") as file:
                fileString = file.read()
            self.updateIncludeFileSegment(scriptType, packageName, fileString)
        else:
            ## If there is just one txt, copy it in then add an include line in our base file
            print ("-- Installing " + scriptType + " file for '" + packageName + "'")
            FileHandler.createFolder(self.getDataFolderForPackage(scriptType, packageName))
            fileNameToInclude = scriptType + "/pk3t/" + packageName + "/" + packageName + ".txt"
            textOfSegment = "#include \"" + fileNameToInclude + "\"\n"
            FileHandler.copyFile(packageFolder + "/" + scriptType + ".txt", self.projectPath + "/pk3/" + fileNameToInclude)
            self.updateIncludeFileSegment(scriptType, packageName, textOfSegment)

    ## Create or overwrite a segment for a package in a top-level project file
    def updateIncludeFileSegment(self, fileNameToUpdate, packageName, textOfSegment):
        filePathToUpdate = self.projectPath + "/pk3/" + fileNameToUpdate + ".pk3t"
        
        stringSegmentStart = "//<< PK3T " + packageName + " START >>//"
        stringSegmentEnd = "//<< PK3T " + packageName + " END >>//"
        
        ##Create our pk3t-recognizable segment
        segment = stringSegmentStart + "\n"
        segment += textOfSegment + "\n"
        segment += stringSegmentEnd + "\n"
        ##If the file doesn't exist, easy - just write it!
        if (not FileHandler.fileExists(filePathToUpdate)):
            with open(filePathToUpdate, 'w') as outfile:
                outfile.write(self.getAutoGeneratedWarning(fileNameToUpdate) + "\n\n")
                outfile.write(segment)
            print ("--- Created " + self.projectPath + " PK3T " + fileNameToUpdate + " file")
            return
        
        ##Otherwise, we have to open the file and either append or replace the existing segment
        with open(filePathToUpdate, 'r') as file:
            newString = ""
            fileString = file.read()
            startIndexOfExistingSegment = fileString.find(stringSegmentStart)
            endIndexOfExistingSegment = fileString.find(stringSegmentEnd) + len(stringSegmentEnd) + 1
            if (startIndexOfExistingSegment == -1):
                newString = fileString + segment
            else:
                newString = fileString[0:startIndexOfExistingSegment] + fileString[endIndexOfExistingSegment:] + segment
        with open(filePathToUpdate, 'w') as outfile:
            outfile.write(newString)
        print ("--- Updated " + self.projectPath + " PK3T " + fileNameToUpdate + " file")
        return
        
    def deleteIncludeFileSegment(self, fileNameToUpdate, packageName):
        
        filePathToUpdate = self.projectPath + "/pk3/" + fileNameToUpdate + ".pk3t"
        
        stringSegmentStart = "//<< PK3T " + packageName + " START >>//"
        stringSegmentEnd = "//<< PK3T " + packageName + " END >>//"
        newString = ""
        
        ##OK, nothing to delete
        if (not FileHandler.fileExists(filePathToUpdate)):
            return
        
        ##Otherwise, open the file and remove the section if it exists
        with open(filePathToUpdate, 'r') as file:
            fileString = file.read()
            startIndexOfExistingSegment = fileString.find(stringSegmentStart)
            endIndexOfExistingSegment = fileString.find(stringSegmentEnd) + len(stringSegmentEnd) + 1
            if (startIndexOfExistingSegment == -1):
                ##No segment - return
                return
            else:
                newString = fileString[0:startIndexOfExistingSegment] + fileString[endIndexOfExistingSegment:]
        with open(filePathToUpdate, 'w') as outfile:
            outfile.write(newString)
        print ("--- Deleted " + self.projectPath + " PK3T " + fileNameToUpdate + " entry for " + packageName)

    def getPackageDescription(self, packageName):
        self.verifyPackage(packageName)
        data = json.load(open(self.LIBRARY_FOLDER + "/" + packageName + "/" + self.PACKAGE_DESCRIPTION_FILE))
        return data
        
    def getProjectDescription(self):
        data = json.load(open(self.projectPath + "/" + self.PROJECT_DESCRIPTION_FILE))
        return data
    
    def saveProjectDescription(self, data):
        with open(self.projectPath + "/" + self.PROJECT_DESCRIPTION_FILE, 'w') as outfile:
            json.dump(data, outfile)
        print ("- Saved " + self.projectPath + " description file")

    def generateMapinfo(self):
        print ("- Updating MAPINFO.pk3t")
        output = self.getAutoGeneratedWarning("MAPINFO")
        output = output + "DoomEdNums {\n"
        projectDescription = self.getProjectDescription()
        installedPackages = projectDescription.get('installed', [])
        for installedPackage in installedPackages:
            desc = self.getPackageDescription(installedPackage)
            doomednums = desc.get("doomednums", {})
            for doomednum, classname in doomednums.items():
                output = output + "    " + doomednum + " = " + classname + "\n"
        output = output + "}\n"
        with open(self.projectPath + "/pk3/mapinfo.pk3t", 'w') as file:
            file.write(output)

    def getAutoGeneratedWarning(self, filetype):
        return ("/////////////////////////////////////////////////////////////\n"
        + "// " + filetype + " generated by PK3Tools!\n"
        + "// Don't modify things here as they'll be overwritten.\n"
        + "// Create your own lump and use it alongside this one instead\n"
        + "/////////////////////////////////////////////////////////////\n\n")
        
    def buildProject(self):
        print ("Zipping project '" + self.projectPath + "'!")
        FileHandler.zipProject(self.projectPath)
        print ("Project '" + self.projectPath + "' built successfully")

    def getDataFolderForPackage(self, dataType, packageName):
        return self.projectPath + "/pk3/" + dataType + "/pk3t/" + packageName
        
    def listPackages(self):
        url = self.REPOSITORY_PREFIX + "/packagelist.php"
        try:
            response = urllib.request.urlopen(url)
        except urllib.error.HTTPError as exception:
            print ("X Failed to contact repository")
            return False
        listedPackages = json.loads(response.read().decode("utf-8"))
        
        installedPackages = []
        if (self.projectPath):
            projectDescription = self.getProjectDescription()
            installedPackages = projectDescription.get('installed', [])
        for packageName in listedPackages:
            flag = " "
            if (packageName in installedPackages):
                flag = "*"
            tagString = ""
            try:
                tagString = " ".join(listedPackages[packageName]['tags'])
            except KeyError:
                pass
            print(flag + " " + packageName.ljust(30) + listedPackages[packageName]['category'].ljust(10) + tagString)
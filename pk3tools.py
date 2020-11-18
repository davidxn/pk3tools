def printHelp():
    print("Available commands:")
    print("")
    print("createproject <project>           - Set up a new project with given name")
    print("buildproject <project>            - Build project into a PK3")
    print("addpackage <project> <package>    - Add package to a project")
    print("removepackage <project> <package> - Remove package from a project")
    print("")
    print("listpackages                      - List packages available in library")
    print("zippackage <package>              - Zip local package for uploading")


if __name__ == "__main__":
    import sys
    from commandhandler import CommandHandler

    myOptions = {}

    print("PK3Tools version " + CommandHandler.VERSION)

    if len(sys.argv) < 2:
        printHelp()
        sys.exit(0)

    myOptions['command'] = sys.argv[1]
    options = sys.argv[2:]
    for i, option in enumerate(options):
        myOptions[i] = option

    pk3tools = CommandHandler(myOptions)
    pk3tools.run()

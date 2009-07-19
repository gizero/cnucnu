#!/usr/bin/python
# vim: fileencoding=utf8 foldmethod=marker
#{{{ License header: GPLv2+
#    This file is part of cnucnu.
#
#    Cnucnu is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    Cnucnu is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with cnucnu.  If not, see <http://www.gnu.org/licenses/>.
#}}}

import sys
import os
sys.path.insert(0, './lib')

from cnucnu.config import Config
from cnucnu.package_list import Repository, PackageList, Package
from cnucnu.checkshell import CheckShell
from cnucnu.bugzilla_reporter import BugzillaReporter

import pprint as pprint_module
pp = pprint_module.PrettyPrinter(indent=4)
pprint = pp.pprint

import pickle

def analyse_packages(packages):
    package_nr = 0

    if package_nr == 0:
        mode = "w"
    else:
        mode = "a"


    outdated_f = open("cnucnu-outdated.log", mode)
    too_new_f = open("cnucnu-too_new.log", mode)
    error_f = open("cnucnu-error.log", mode)

    for package in packages[package_nr:]:
        sys.stderr.write("Testing: %i -  %s\n" % (package_nr, package.name))

        try:
            if package.upstream_newer:
                print "Outdated package %(name)s: Rawhide version: %(repo_version)s, Upstream latest: %(latest_upstream)s" % package
                outdated_f.write("%(name)s %(repo_version)s %(latest_upstream)s\n" % package)
            elif package.repo_newer:
                print "Rawhide newer %(name)s: Rawhide version: %(repo_version)s, Upstream latest: %(latest_upstream)s" % package
                too_new_f.write("%(name)s %(repo_version)s %(latest_upstream)s\n" % package)

        except cc_errors.UpstreamVersionRetrievalError, e:
            sys.stderr.write("%s\n" % str(e))
            sys.stderr.write("Rawhide Version: %s\n" % package.repo_version)
            error_f.write("%s: %s - Rawhide Version: %s\n" % (package.name, str(e), package.repo_version))
        except KeyError, ke:
            sys.stderr.write("Package not found in Rawhide: %s\n" % str(ke))

        package_nr = package_nr + 1

    outdated_f.close()
    too_new_f.close()
    error_f.close()
    pickle_file = open("data.pickle", "wb")
    pickle.dump(packages, pickle_file)
    pickle_file.close()

if __name__ == '__main__':
    import re
    import cnucnu.errors as cc_errors

    from optparse import OptionParser
    parser = OptionParser()
     
    parser.add_option("", "--shell", dest="action", help="Interactive shell", action="store_const", const="shell")
    parser.add_option("", "--config", dest="config_filename", help="config_filename, e.g. for bugzilla credentials")
    parser.add_option("", "--create-bugs", dest="action", help="file bugs for outdated packages", action="store_const", const="create-bugs")
    parser.add_option("", "--fm-outdated-all", dest="action", help="compare all packages in rawhide with freshmeat", action="store_const", const="fm-outdated-all")
    parser.add_option("", "--dump-config", dest="action", help="dumps dconfig to stdout", action="store_const", const="dump-config")
    parser.add_option("", "--dump-default-config", dest="action", help="dumps default config to stdout", action="store_const", const="dump-default-config")
    parser.add_option("", "--dry-run", dest="dry_run", help="Do not file or change bugs", default=False)

    (options, args) = parser.parse_args()

    config = Config()

    if options.action == "dump-default-config":
        sys.stdout.write(config.yaml)
        sys.exit(0)

    yaml_file = options.config_filename
    if not yaml_file:
        new_yaml_file = "./cnucnu.yaml"
        if os.access(new_yaml_file, os.R_OK):
            yaml_file = new_yaml_file

    if yaml_file:
        config.update_yaml_file(yaml_file)
    
    if options.action == "dump-config":
        sys.stdout.write(config.yaml)
        sys.exit(0)

    if options.action == "shell":
        shell = CheckShell(config=config)
        while True:
            try:
                if not shell.cmdloop():
                    break
            except Exception, ex: 
                print 'Exception occured:'
                print repr(ex)
                break
    elif options.action == "create-bugs":
        bugzilla_config =  config.bugzilla_config
        br = BugzillaReporter(bugzilla_config)

        repo = Repository(**config.config["repo"])
        pl = PackageList(repo=repo, **config.config["package list"])
        for p in pl:
            print "testing: %s" % p.name
            try:
                if p.upstream_newer:
                    br.report_outdated(p, dry_run=options.dry_run)
            except Exception, e:
                pprint(e)
    elif options.action == "fm-outdated-all":
        print "checking all against FM"
        repo = Repository()
        package_names = [name for name in repo.repoquery()]
        pl=[Package(name, "FM-DEFAULT", "FM-DEFAULT", repo) for name in package_names]
        packages = PackageList(packages=pl)
        repo.package_list = packages
        analyse_packages(packages)

    else:
        print "default..."
        repo = Repository()
        plist = PackageList(repo=repo)
        packages = plist.packages
        analyse_packages(packages)

# Contributing to pyadi-iio

When contributing to this repository, please first discuss the change you wish to make via the
[issue tracker](https://github.com/analogdevicesinc/pyadi-iio/issues) before making a pull request.

Please note we have a code of conduct, please follow it in all your interactions with the project.

The [pyadi-iio repository](https://github.com/analogdevicesinc/pyadi-iio) is a aggregate of a module
and separate applications/programs/examples as well as doc which use that module:
* All components are licensed under the ADI-BSD license found in the root of the repository

Any pull requests will be covered by this license.

## Pull Request Checklist

1. Commit message includes a "Signed-off-by: [name] < email >" to the commit message.
   This ensures you have the rights to submit your code, by agreeing to the
   [Developer Certificate of Origin](https://developercertificate.org/). If you can not agree to
   the DCO, don't submit a pull request, as we can not accept it.
2. Commit should be "atomic", ie : should do one thing only. A pull requests should only contain
   multiple commits if that is required to fix the bug or implement the feature.
3. Commits should have good commit messages. Check out [The git Book](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project)
   for some pointers, and tools to use.
4. All code should be formatted using the recommended tools in the doc and pass all linter checks
5. All currently passing test should pass that run within the CI environment

## Pull Request Process

1. Make a fork, if you are not sure on how to make a fork, check out [GitHub help](https://help.github.com/en/github/getting-started-with-github/fork-a-repo)
2. Make a Pull Request, if you are not sure on how to make a pull request, check out [GitHub help](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)
3. Before a Pull Request can be merged, it must be reviewd by at least one reviewer, and tested on as
   the target hardware(s). The hardware used to test a commit should be noted in the Pull Request.

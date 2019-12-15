### NYCMeshBot

The NYCMeshBot is a Django based Slackbot.

![](https://img.shields.io/github/stars/nycmeshnet/nycmeshbot.svg) ![](https://img.shields.io/github/forks/nycmeshnet/nycmeshbot.svg) ![](https://img.shields.io/github/tag/nycmeshnet/nycmeshbot.svg) ![](https://img.shields.io/github/issues/nycmeshnet/nycmeshbot.svg) ![](https://img.shields.io/github/license/nycmeshnet/nycmeshbot.svg)


#### Highlights
- Docker based for easy and repeatable dev and prod deployments
- Django based, making it easy for Python developers to contribute
- Interacts with the [NYCMesh API](https://github.com/nycmeshnet/nycmesh-api "NYCMesh API")
- Supports Interactive actions in a post
- Supports Slack Modal Windows (40% complete)

#### Development

If you're looking to help with development, fork the repo and use [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) model to create new feature branches for each new feature you add. `develop` branch is the default branch and should be considered unstable. All feature/release branches use `develop` as the base, NOT `master`. Master branch is only used for tagging new releases and should be considered stable. Hotfix branches will base from `master` and should be merged into `master` and back-merged into `develop`. Any PR's that are submitted should PR against either `develop` or any relevant `release/` branch.

You will need docker to stand up your development environment, unless you really want to do it the harder way and build a server/vm. Once you clone the repo, you'll automatically be in the `develop` branch. To stand up the dev environment, just run 

    docker-compose -f docker-compose.dev.yml build
    docker-compose -f docker-compose.dev.yml up -d

You can then access the bot API over `http://localhost:8000`

#### Deployment

When we're ready to deploy a new release, the `release/` branch is merged into `master` and back-merged into `develop`. Clean up any merge conflicts. Then tag the release and push the tags to the repo. Once a new tag is published, Github Actions will login to the server and auto-build the new containers, then deploy them. You can see how this works by [viewing the action yourself](https://github.com/nycmeshnet/nycmeshbot/blob/develop/.github/workflows/main.yml).

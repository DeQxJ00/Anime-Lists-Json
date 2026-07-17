# AniDB Static JSON API for GitHub Pages

这个目录可以直接发布到 GitHub Pages。它把 Anime-Lists 的 `anime-list-master.xml` 预生成成静态 JSON 文件。

## API

```text
GET /api/anidb/{anidbid}.json
GET /api/imdb/{imdbid}.json
```

示例：

```text
GET /api/anidb/1.json
GET /api/imdb/tt0119698.json
```

返回该 ID 对应的完整 `anime` 信息，字段来自 XML 的属性和子节点。`imdbid` 如果对应多条 anime，会返回数组。

## 查询页

打开站点首页输入 AniDB ID 即可查询。也可以使用：

```text
/?id=1
```

## 重新生成

先下载最新 XML：

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list-master.xml" -OutFile "anime-list-master.xml"
```

然后生成 JSON：

```powershell
python tools/build_static_api.py --xml anime-list-master.xml --out .
```

## 自动更新

已经包含 GitHub Actions 工作流：

```text
.github/workflows/update-static-api.yml
```

它会每天拉取一次上游：

```text
https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list-master.xml
```

Action 会先查询上游 `anime-list-master.xml` 最近一次变更的 commit。没有变化时会直接结束，不下载 XML，也不运行生成脚本；有变化时才重新生成：

```text
api/anidb/{anidbid}.json
api/anidb/index.json
api/imdb/{imdbid}.json
api/imdb/index.json
```

如果 JSON 有变化，Action 会先拉取远端最新分支，再自动提交到当前仓库。也可以在 GitHub Actions 页面手动点 `Run workflow` 立即同步。

## 部署到 GitHub Pages

1. 把本目录内容提交到 GitHub 仓库。
2. 在仓库 Settings -> Pages 选择部署分支。
3. 访问 `https://<username>.github.io/<repo>/api/anidb/1.json` 或 `https://<username>.github.io/<repo>/api/imdb/tt0119698.json`。

注意：GitHub Pages 是纯静态托管，不能运行后端代码。因此这里用预生成 JSON 文件实现 API。

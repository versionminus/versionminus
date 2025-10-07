# licodex: live coding exercise for a GenAI powered note-taking app

## about

This repository contains a live coding exercise for building a GenAI powered note-taking application called "licodex". The application allows users to create, manage, and search notes using natural language processing and AI capabilities.

## TODOs

- meaningful errors, e.g.: no user found on new note creation
- verify that all router methods follow the pattern: schema -> router -> service -> repo -> model
- implement soft deletes in all models
- implement garbage collector for soft deleted items
- finish milvus setup: siphonn.utils -> licodex.core.config (get ConfigStore values)
- container for react
- nginx for CORS
- verify if we can remove licodex.core.milvus
- (embeddings router) verify different ordering of payload arrays: Silent misalignment of data. Always derive order from `coll.schema.fields`
- create a pluggable provider system (Provider enum + factory)
QueuedUrl
-----
- id: any
- url: string
- level: int

Url
-----
- id : int/hash
- url : string
- level: int
- status : int
- visited : datetime
- children : [Url]

Web
-----
- root: Url

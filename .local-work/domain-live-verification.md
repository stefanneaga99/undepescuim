# unde-pescuim.ro live domain verification

- checkedAt: `2026-08-25T09:57:25.435907+00:00`
- Scope: read-only public DNS, HTTP and TLS probes; no mutations.

## Commands and exact responses

### NS delegation and DNSSEC
#### Cloudflare DoH
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=NS` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":2}],"Answer":[{"name":"unde-pescuim.ro","type":2,"TTL":86400,"data":"sky.ns.cloudflare.com."},{"name":"unde-pescuim.ro","type":2,"TTL":86400,"data":"beau.ns.cloudflare.com."}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=DS` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":43}],"Answer":[{"name":"unde-pescuim.ro","type":43,"TTL":86400,"data":"2371 13 2 111a1861d6dfd0bb619c5200f991982ea806c6d074a8e56ec50ce409dd9f5aa3"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=DNSKEY` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":48}],"Answer":[{"name":"unde-pescuim.ro","type":48,"TTL":2930,"data":"256 3 13 oJMRESz5E4gYzS/q6XDrvU1qMPYIjCWzJaOau8XNEZeqCYKD5ar0IRd8KqXXFJkqmVfRvMGPmM1x8fGAa2XhSA=="},{"name":"unde-pescuim.ro","type":48,"TTL":2930,"data":"257 3 13 mdsswUyr3DPW132mOi8V9xESWE8jTo0dxCjjnopKl+GqJxpVXckHAeF+KkxLbxILfDLUT0rAK9iUzy1L53eKGQ=="}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=RRSIG` -> HTTP 200
```json
{"Status":2,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":46}],"Comment":["EDE(21): Not Supported RRSIG queries not supported here","EDE(22): No Reachable Authority at delegation unde-pescuim.ro."]}
```
#### Google DoH
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=NS` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":2}],"Answer":[{"name":"unde-pescuim.ro.","type":2,"TTL":21600,"data":"sky.ns.cloudflare.com."},{"name":"unde-pescuim.ro.","type":2,"TTL":21600,"data":"beau.ns.cloudflare.com."}],"Comment":"Response from 108.162.193.73."}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=DS` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":43}],"Answer":[{"name":"unde-pescuim.ro.","type":43,"TTL":21600,"data":"2371 13 2 111A1861D6DFD0BB619C5200F991982EA806C6D074A8E56EC50CE409DD9F5AA3"}],"Comment":"Response from 78.104.145.6."}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=DNSKEY` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":48}],"Answer":[{"name":"unde-pescuim.ro.","type":48,"TTL":3600,"data":"256 3 13 oJMRESz5E4gYzS/q6XDrvU1qMPYIjCWzJaOau8XNEZeqCYKD5ar0IRd8KqXXFJkqmVfRvMGPmM1x8fGAa2XhSA=="},{"name":"unde-pescuim.ro.","type":48,"TTL":3600,"data":"257 3 13 mdsswUyr3DPW132mOi8V9xESWE8jTo0dxCjjnopKl+GqJxpVXckHAeF+KkxLbxILfDLUT0rAK9iUzy1L53eKGQ=="}],"Comment":"Response from 172.64.33.73."}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=RRSIG` -> HTTP 200
```json
{"Status":2,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":46}],"Comment":"Name servers refused query (lame delegation?) [108.162.193.73, 173.245.59.73, 108.162.194.2, 172.64.34.2, 172.64.33.73, 162.159.38.2].","extended_dns_errors":[{"info_code":23,"extra_text":"[108.162.193.73] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":23,"extra_text":"[173.245.59.73] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":23,"extra_text":"[108.162.194.2] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":23,"extra_text":"[172.64.34.2] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":23,"extra_text":"[172.64.33.73] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":23,"extra_text":"[162.159.38.2] rcode=REFUSED for unde-pescuim.ro/rrsig"},{"info_code":22,"extra_text":"At delegation unde-pescuim.ro for unde-pescuim.ro/rrsig"}]}
```
### Apex and www resolution
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=A` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":1}],"Answer":[{"name":"unde-pescuim.ro","type":1,"TTL":300,"data":"64.29.17.65"},{"name":"unde-pescuim.ro","type":1,"TTL":300,"data":"216.198.79.65"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=AAAA` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":28}],"Authority":[{"name":"unde-pescuim.ro","type":6,"TTL":1800,"data":"beau.ns.cloudflare.com. dns.cloudflare.com. 2413057894 10000 2400 604800 1800"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=CNAME` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":5}],"Authority":[{"name":"unde-pescuim.ro","type":6,"TTL":1787,"data":"beau.ns.cloudflare.com. dns.cloudflare.com. 2413057894 10000 2400 604800 1800"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=www.unde-pescuim.ro&type=A` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"www.unde-pescuim.ro","type":1}],"Answer":[{"name":"www.unde-pescuim.ro","type":5,"TTL":300,"data":"ef9fdab2479440b3.vercel-dns-017.com."},{"name":"ef9fdab2479440b3.vercel-dns-017.com","type":1,"TTL":300,"data":"216.198.79.65"},{"name":"ef9fdab2479440b3.vercel-dns-017.com","type":1,"TTL":300,"data":"64.29.17.65"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=www.unde-pescuim.ro&type=AAAA` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"www.unde-pescuim.ro","type":28}],"Answer":[{"name":"www.unde-pescuim.ro","type":5,"TTL":287,"data":"ef9fdab2479440b3.vercel-dns-017.com."}],"Authority":[{"name":"vercel-dns-017.com","type":6,"TTL":887,"data":"ns1.vercel-dns-017.com. awsdns-hostmaster.amazon.com. 1 3600 900 1209600 900"}]}
```
`GET https://cloudflare-dns.com/dns-query?name=www.unde-pescuim.ro&type=CNAME` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"www.unde-pescuim.ro","type":5}],"Answer":[{"name":"www.unde-pescuim.ro","type":5,"TTL":300,"data":"ef9fdab2479440b3.vercel-dns-017.com."}]}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=A` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":1}],"Answer":[{"name":"unde-pescuim.ro.","type":1,"TTL":286,"data":"64.29.17.65"},{"name":"unde-pescuim.ro.","type":1,"TTL":286,"data":"216.198.79.65"}]}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=AAAA` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":28}],"Authority":[{"name":"unde-pescuim.ro.","type":6,"TTL":1800,"data":"beau.ns.cloudflare.com. dns.cloudflare.com. 2413057894 10000 2400 604800 1800"}],"Comment":"Response from 108.162.193.73."}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=CNAME` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":5}],"Authority":[{"name":"unde-pescuim.ro.","type":6,"TTL":1799,"data":"beau.ns.cloudflare.com. dns.cloudflare.com. 2413057894 10000 2400 604800 1800"}]}
```
`GET https://dns.google/resolve?name=www.unde-pescuim.ro&type=A` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"www.unde-pescuim.ro.","type":1}],"Answer":[{"name":"www.unde-pescuim.ro.","type":5,"TTL":300,"data":"ef9fdab2479440b3.vercel-dns-017.com."},{"name":"ef9fdab2479440b3.vercel-dns-017.com.","type":1,"TTL":300,"data":"216.198.79.65"},{"name":"ef9fdab2479440b3.vercel-dns-017.com.","type":1,"TTL":300,"data":"64.29.17.65"}],"Comment":"Response from 2600:9000:5304:a800::1."}
```
`GET https://dns.google/resolve?name=www.unde-pescuim.ro&type=AAAA` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":false,"CD":false,"Question":[{"name":"www.unde-pescuim.ro.","type":28}],"Answer":[{"name":"www.unde-pescuim.ro.","type":5,"TTL":286,"data":"ef9fdab2479440b3.vercel-dns-017.com."}],"Authority":[{"name":"vercel-dns-017.com.","type":6,"TTL":900,"data":"ns1.vercel-dns-017.com. awsdns-hostmaster.amazon.com. 1 3600 900 1209600 900"}],"Comment":"Response from 2600:9000:5301:d300::1."}
```
`GET https://dns.google/resolve?name=www.unde-pescuim.ro&type=CNAME` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"www.unde-pescuim.ro.","type":5}],"Answer":[{"name":"www.unde-pescuim.ro.","type":5,"TTL":286,"data":"ef9fdab2479440b3.vercel-dns-017.com."}]}
```
### HTTP/HTTPS probes
`curl --http1.1 -sS -D - -o /dev/null --max-time 30 https://unde-pescuim.ro` -> exit 0
```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 84408
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline
Content-Length: 25748
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: text/html; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:27 GMT
Etag: "a7b1f8725ae38d2c65681e5ef2aec1c3"
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
X-Frame-Options: DENY
X-Matched-Path: /
X-Nextjs-Prerender: 1
X-Nextjs-Stale-Time: 300
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::wq2rn-1787651847843-b61b8ef830ad


```
`curl --http1.1 -sS -D - -o /dev/null --max-time 30 http://unde-pescuim.ro` -> exit 0
```
HTTP/1.0 308 Permanent Redirect
Content-Type: text/plain
Location: https://unde-pescuim.ro/
Refresh: 0;url=https://unde-pescuim.ro/
server: Vercel


```
`curl --http1.1 -sS -D - -o /dev/null --max-time 30 https://www.unde-pescuim.ro` -> exit 0
```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 84423
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline
Content-Length: 25748
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: text/html; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "a7b1f8725ae38d2c65681e5ef2aec1c3"
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
X-Frame-Options: DENY
X-Matched-Path: /
X-Nextjs-Prerender: 1
X-Nextjs-Stale-Time: 300
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::qd4vf-1787651848051-5e78059e9169


```
`curl --http1.1 -sS -D - -o /dev/null --max-time 30 http://www.unde-pescuim.ro` -> exit 0
```
HTTP/1.0 308 Permanent Redirect
Content-Type: text/plain
Location: https://www.unde-pescuim.ro/
Refresh: 0;url=https://www.unde-pescuim.ro/
server: Vercel


```
`curl --http1.1 -sS -D - -o /dev/null --max-time 30 https://undepescuim.vercel.app` -> exit 0
```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 356345
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline
Content-Length: 25748
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: text/html; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "a7b1f8725ae38d2c65681e5ef2aec1c3"
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
X-Frame-Options: DENY
X-Matched-Path: /
X-Nextjs-Prerender: 1
X-Nextjs-Stale-Time: 300
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::8llmt-1787651848323-89361b15d08d


```
`curl --http1.1 -sS -L -D - --max-time 30 https://unde-pescuim.ro/robots.txt` -> exit 0
```
HTTP/1.1 404 Not Found
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 87706
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline; filename="404"
Content-Length: 9557
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: text/html; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "33de37c25a49ebe0c539d29d47b71972"
Last-Modified: Mon, 24 Aug 2026 09:35:41 GMT
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Matched-Path: /404
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::vqpf2-1787651848474-9fcf21c039ac

<!DOCTYPE html><html lang="ro" class="__variable_246ccd __variable_c29908 h-full antialiased"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/><link rel="preload" href="/_next/static/media/22a5144ee8d83bca-s.p.woff2" as="font" crossorigin="" type="font/woff2"/><link rel="preload" href="/_next/static/media/7d4881bb7e1bf84d-s.p.woff2" as="font" crossorigin="" type="font/woff2"/><link rel="stylesheet" href="/_next/static/css/c266bafc6be55bdd.css" data-precedence="next"/><link rel="preload" as="script" fetchPriority="low" href="/_next/static/chunks/webpack-29dfff985d9615ad.js"/><script src="/_next/static/chunks/4bd1b696-58970b7b91aecaf4.js" async=""></script><script src="/_next/static/chunks/755-e4165778069a79e3.js" async=""></script><script src="/_next/static/chunks/main-app-bbb628e2674b0dcf.js" async=""></script><script src="/_next/static/chunks/531-c25ea46aed656dbf.js" async=""></script><script src="/_next/static/chunks/app/layout-845e011fbacfcfce.js" async=""></script><meta name="robots" content="noindex"/><meta name="theme-color" content="#171717"/><meta name="color-scheme" content="light dark"/><title>UndePescuim.ro</title><meta name="description" content="Harta apelor de pescuit contractate din România — contracted fishing waters in Romania"/><link rel="manifest" href="/manifest.webmanifest"/><meta name="mobile-web-app-capable" content="yes"/><meta name="apple-mobile-web-app-title" content="UndePescuim"/><meta name="apple-mobile-web-app-status-bar-style" content="default"/><link rel="icon" href="/favicon.ico?603d046c9a6fdfbb" type="image/x-icon" sizes="16x16"/><link rel="apple-touch-icon" href="/icons/apple-touch-icon-180x180.png" sizes="180x180" type="image/png"/><meta name="next-size-adjust" content=""/><title>404: This page could not be found.</title><script src="/_next/static/chunks/polyfills-42372ed130431b0a.js" noModule=""></script></head><body class="min-h-full flex flex-col overscroll-none"><div hidden=""><!--$--><!--/$--></div><script>((a,b,c,d,e,f,g,h)=>{let i=document.documentElement,j=["light","dark"];function k(b){var c;(Array.isArray(a)?a:[a]).forEach(a=>{let c="class"===a,d=c&&f?e.map(a=>f[a]||a):e;c?(i.classList.remove(...d),i.classList.add(f&&f[b]?f[b]:b)):i.setAttribute(a,b)}),c=b,h&&j.includes(c)&&(i.style.colorScheme=c)}if(d)k(d);else try{let a=localStorage.getItem(b)||c,d=g&&"system"===a?window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light":a;k(d)}catch(a){}})("class","theme","system",null,["light","dark"],null,true,true)</script><div style="font-family:system-ui,&quot;Segoe UI&quot;,Roboto,Helvetica,Arial,sans-serif,&quot;Apple Color Emoji&quot;,&quot;Segoe UI Emoji&quot;;height:100vh;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center"><div><style>body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}</style><h1 class="next-error-h1" style="display:inline-block;margin:0 20px 0 0;padding:0 23px 0 0;font-size:24px;font-weight:500;vertical-align:top;line-height:49px">404</h1><div style="display:inline-block"><h2 style="font-size:14px;font-weight:400;line-height:49px;margin:0">This page could not be found.</h2></div></div></div><!--$--><!--/$--><script src="/_next/static/chunks/webpack-29dfff985d9615ad.js" id="_R_" async=""></script><script>(self.__next_f=self.__next_f||[]).push([0])</script><script>self.__next_f.push([1,"1:\"$Sreact.fragment\"\n2:I[460,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"ThemeProvider\"]\n3:I[5531,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"I18nProvider\"]\n4:I[7121,[],\"\"]\n5:I[4581,[],\"\"]\n6:I[3647,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"ServiceWorkerRegister\"]\n7:I[484,[],\"OutletBoundary\"]\n8:\"$Sreact.suspense\"\nb:I[484,[],\"ViewportBoundary\"]\nd:I[484,[],\"MetadataBoundary\"]\nf:I[7123,[],\"default\",1]\n:HL[\"/_next/static/media/22a5144ee8d83bca-s.p.woff2\",\"font\",{\"crossOrigin\":\"\",\"type\":\"font/woff2\"}]\n:HL[\"/_next/static/media/7d4881bb7e1bf84d-s.p.woff2\",\"font\",{\"crossOrigin\":\"\",\"type\":\"font/woff2\"}]\n:HL[\"/_next/static/css/c266bafc6be55bdd.css\",\"style\"]\na:X\n0:{\"P\":null,\"c\":[\"\",\"_not-found\"],\"q\":\"\",\"i\":false,\"f\":[[[\"\",{\"children\":[\"_not-found\",{\"children\":[\"__PAGE__\",{},\"$undefined\",\"$undefined\",4608]},\"$undefined\",\"$undefined\",4608]},\"$undefined\",\"$undefined\",4624],[[\"$\",\"$1\",\"c\",{\"children\":[[[\"$\",\"link\",\"0\",{\"rel\":\"stylesheet\",\"href\":\"/_next/static/css/c266bafc6be55bdd.css\",\"precedence\":\"next\",\"crossOrigin\":\"$undefined\",\"nonce\":\"$undefined\"}]],[\"$\",\"html\",null,{\"lang\":\"ro\",\"suppressHydrationWarning\":true,\"className\":\"__variable_246ccd __variable_c29908 h-full antialiased\",\"children\":[\"$\",\"body\",null,{\"className\":\"min-h-full flex flex-col overscroll-none\",\"children\":[[\"$\",\"$L2\",null,{\"attribute\":\"class\",\"defaultTheme\":\"system\",\"enableSystem\":true,\"disableTransitionOnChange\":true,\"children\":[\"$\",\"$L3\",null,{\"children\":[\"$\",\"$L4\",null,{\"parallelRouterKey\":\"children\",\"error\":\"$undefined\",\"errorStyles\":\"$undefined\",\"errorScripts\":\"$undefined\",\"template\":[\"$\",\"$L5\",null,{}],\"templateStyles\":\"$undefined\",\"templateScripts\":\"$undefined\",\"notFound\":\"$undefined\",\"forbidden\":\"$undefined\",\"unauthorized\":\"$undefined\"}]}]}],[\"$\",\"$L6\",null,{}]]}]}]]}],{\"children\":[[\"$\",\"$1\",\"c\",{\"children\":[null,[\"$\",\"$L4\",null,{\"parallelRouterKey\":\"children\",\"error\":\"$undefined\",\"errorStyles\":\"$undefined\",\"errorScripts\":\"$undefined\",\"template\":[\"$\",\"$L5\",null,{}],\"templateStyles\":\"$undefined\",\"templateScripts\":\"$undefined\",\"notFound\":\"$undefined\",\"forbidden\":\"$undefined\",\"unauthorized\":\"$undefined\"}]]}],{\"children\":[[\"$\",\"$1\",\"c\",{\"children\":[[[\"$\",\"title\",null,{\"children\":\"404: This page could not be found.\"}],[\"$\",\"div\",null,{\"style\":{\"fontFamily\":\"system-ui,\\\"Segoe UI\\\",Roboto,Helvetica,Arial,sans-serif,\\\"Apple Color Emoji\\\",\\\"Segoe UI Emoji\\\"\",\"height\":\"100vh\",\"textAlign\":\"center\",\"display\":\"flex\",\"flexDirection\":\"column\",\"alignItems\":\"center\",\"justifyContent\":\"center\"},\"children\":[\"$\",\"div\",null,{\"children\":[[\"$\",\"style\",null,{\"dangerouslySetInnerHTML\":{\"__html\":\"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}\"}}],[\"$\",\"h1\",null,{\"className\":\"next-error-h1\",\"style\":{\"display\":\"inline-block\",\"margin\":\"0 20px 0 0\",\"padding\":\"0 23px 0 0\",\"fontSize\":24,\"fontWeight\":500,\"verticalAlign\":\"top\",\"lineHeight\":\"49px\"},\"children\":404}],[\"$\",\"div\",null,{\"style\":{\"display\":\"inline-block\"},\"children\":[\"$\",\"h2\",null,{\"style\":{\"fontSize\":14,\"fontWeight\":400,\"lineHeight\":\"49px\",\"margin\":0},\"children\":\"This page could not be found.\"}]}]]}]}]],null,[\"$\",\"$L7\",null,{\"children\":[\"$\",\"$8\",null,{\"name\":\"Next.MetadataOutlet\",\"children\":\"$@9\"}]}]]}],{},null,false,null]},null,false,\"$a\"]},null,false,null],[\"$\",\"$1\",\"h\",{\"children\":[[\"$\",\"meta\",null,{\"name\":\"robots\",\"content\":\"noindex\"}],[\"$\",\"$Lb\",null,{\"children\":\"$Lc\"}],[\"$\",\"div\",null,{\"hidden\":true,\"children\":[\"$\",\"$Ld\",null,{\"children\":[\"$\",\"$8\",null,{\"name\":\"Next.Metadata\",\"children\":\"$Le\"}]}]}],[\"$\",\"meta\",null,{\"name\":\"next-size-adjust\",\"content\":\"\"}]]}],false]],\"m\":\"$undefined\",\"G\":[\"$f\",[]],\"S\":true,\"h\":null,\"r\":\"$undefined\",\"s\":\"$undefined\",\"a\":\"$undefined\",\"l\":\"$undefined\",\"p\":\"$undefined\",\"d\":\"$undefined\",\"b\":\"0WOlzqy4CsZ_r76w9-qKO\"}\na:C\nc:[[\"$\",\"meta\",\"0\",{\"charSet\":\"utf-8\"}],[\"$\",\"meta\",\"1\",{\"name\":\"viewport\",\"content\":\"width=device-width, initial-scale=1, viewport-fit=cover\"}],[\"$\",\"meta\",\"2\",{\"name\":\"theme-color\",\"content\":\"#171717\"}],[\"$\",\"meta\",\"3\",{\"name\":\"color-scheme\",\"content\":\"light dark\"}]]\n10:I[6869,[],\"IconMark\"]\n9:null\ne:[[\"$\",\"title\",\"0\",{\"children\":\"UndePescuim.ro\"}],[\"$\",\"meta\",\"1\",{\"name\":\"description\",\"content\":\"Harta apelor de pescuit contractate din România — contracted fishing waters in Romania\"}],[\"$\",\"link\",\"2\",{\"rel\":\"manifest\",\"href\":\"/manifest.webmanifest\",\"crossOrigin\":\"$undefined\"}],[\"$\",\"meta\",\"3\",{\"name\":\"mobile-web-app-capable\",\"content\":\"yes\"}],[\"$\",\"meta\",\"4\",{\"name\":\"apple-mobile-web-app-title\",\"content\":\"UndePescuim\"}],[\"$\",\"meta\",\"5\",{\"name\":\"apple-mobile-web-app-status-bar-style\",\"content\":\"default\"}],[\"$\",\"link\",\"6\",{\"rel\":\"icon\",\"href\":\"/favicon.ico?603d046c9a6fdfbb\",\"type\":\"image/x-icon\",\"sizes\":\"16x16\"}],[\"$\",\"link\",\"7\",{\"rel\":\"apple-touch-icon\",\"href\":\"/icons/apple-touch-icon-180x180.png\",\"sizes\":\"180x180\",\"type\":\"image/png\"}],[\"$\",\"$L10\",\"8\",{}]]\n"])</script></body></html>

```
`curl --http1.1 -sS -L -D - --max-time 30 https://unde-pescuim.ro/sitemap.xml` -> exit 0
```
HTTP/1.1 404 Not Found
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 87706
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline; filename="404"
Content-Length: 9557
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: text/html; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "33de37c25a49ebe0c539d29d47b71972"
Last-Modified: Mon, 24 Aug 2026 09:35:41 GMT
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Matched-Path: /404
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::6dhfz-1787651848601-4ec9c2327358

<!DOCTYPE html><html lang="ro" class="__variable_246ccd __variable_c29908 h-full antialiased"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/><link rel="preload" href="/_next/static/media/22a5144ee8d83bca-s.p.woff2" as="font" crossorigin="" type="font/woff2"/><link rel="preload" href="/_next/static/media/7d4881bb7e1bf84d-s.p.woff2" as="font" crossorigin="" type="font/woff2"/><link rel="stylesheet" href="/_next/static/css/c266bafc6be55bdd.css" data-precedence="next"/><link rel="preload" as="script" fetchPriority="low" href="/_next/static/chunks/webpack-29dfff985d9615ad.js"/><script src="/_next/static/chunks/4bd1b696-58970b7b91aecaf4.js" async=""></script><script src="/_next/static/chunks/755-e4165778069a79e3.js" async=""></script><script src="/_next/static/chunks/main-app-bbb628e2674b0dcf.js" async=""></script><script src="/_next/static/chunks/531-c25ea46aed656dbf.js" async=""></script><script src="/_next/static/chunks/app/layout-845e011fbacfcfce.js" async=""></script><meta name="robots" content="noindex"/><meta name="theme-color" content="#171717"/><meta name="color-scheme" content="light dark"/><title>UndePescuim.ro</title><meta name="description" content="Harta apelor de pescuit contractate din România — contracted fishing waters in Romania"/><link rel="manifest" href="/manifest.webmanifest"/><meta name="mobile-web-app-capable" content="yes"/><meta name="apple-mobile-web-app-title" content="UndePescuim"/><meta name="apple-mobile-web-app-status-bar-style" content="default"/><link rel="icon" href="/favicon.ico?603d046c9a6fdfbb" type="image/x-icon" sizes="16x16"/><link rel="apple-touch-icon" href="/icons/apple-touch-icon-180x180.png" sizes="180x180" type="image/png"/><meta name="next-size-adjust" content=""/><title>404: This page could not be found.</title><script src="/_next/static/chunks/polyfills-42372ed130431b0a.js" noModule=""></script></head><body class="min-h-full flex flex-col overscroll-none"><div hidden=""><!--$--><!--/$--></div><script>((a,b,c,d,e,f,g,h)=>{let i=document.documentElement,j=["light","dark"];function k(b){var c;(Array.isArray(a)?a:[a]).forEach(a=>{let c="class"===a,d=c&&f?e.map(a=>f[a]||a):e;c?(i.classList.remove(...d),i.classList.add(f&&f[b]?f[b]:b)):i.setAttribute(a,b)}),c=b,h&&j.includes(c)&&(i.style.colorScheme=c)}if(d)k(d);else try{let a=localStorage.getItem(b)||c,d=g&&"system"===a?window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light":a;k(d)}catch(a){}})("class","theme","system",null,["light","dark"],null,true,true)</script><div style="font-family:system-ui,&quot;Segoe UI&quot;,Roboto,Helvetica,Arial,sans-serif,&quot;Apple Color Emoji&quot;,&quot;Segoe UI Emoji&quot;;height:100vh;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center"><div><style>body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}</style><h1 class="next-error-h1" style="display:inline-block;margin:0 20px 0 0;padding:0 23px 0 0;font-size:24px;font-weight:500;vertical-align:top;line-height:49px">404</h1><div style="display:inline-block"><h2 style="font-size:14px;font-weight:400;line-height:49px;margin:0">This page could not be found.</h2></div></div></div><!--$--><!--/$--><script src="/_next/static/chunks/webpack-29dfff985d9615ad.js" id="_R_" async=""></script><script>(self.__next_f=self.__next_f||[]).push([0])</script><script>self.__next_f.push([1,"1:\"$Sreact.fragment\"\n2:I[460,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"ThemeProvider\"]\n3:I[5531,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"I18nProvider\"]\n4:I[7121,[],\"\"]\n5:I[4581,[],\"\"]\n6:I[3647,[\"531\",\"static/chunks/531-c25ea46aed656dbf.js\",\"177\",\"static/chunks/app/layout-845e011fbacfcfce.js\"],\"ServiceWorkerRegister\"]\n7:I[484,[],\"OutletBoundary\"]\n8:\"$Sreact.suspense\"\nb:I[484,[],\"ViewportBoundary\"]\nd:I[484,[],\"MetadataBoundary\"]\nf:I[7123,[],\"default\",1]\n:HL[\"/_next/static/media/22a5144ee8d83bca-s.p.woff2\",\"font\",{\"crossOrigin\":\"\",\"type\":\"font/woff2\"}]\n:HL[\"/_next/static/media/7d4881bb7e1bf84d-s.p.woff2\",\"font\",{\"crossOrigin\":\"\",\"type\":\"font/woff2\"}]\n:HL[\"/_next/static/css/c266bafc6be55bdd.css\",\"style\"]\na:X\n0:{\"P\":null,\"c\":[\"\",\"_not-found\"],\"q\":\"\",\"i\":false,\"f\":[[[\"\",{\"children\":[\"_not-found\",{\"children\":[\"__PAGE__\",{},\"$undefined\",\"$undefined\",4608]},\"$undefined\",\"$undefined\",4608]},\"$undefined\",\"$undefined\",4624],[[\"$\",\"$1\",\"c\",{\"children\":[[[\"$\",\"link\",\"0\",{\"rel\":\"stylesheet\",\"href\":\"/_next/static/css/c266bafc6be55bdd.css\",\"precedence\":\"next\",\"crossOrigin\":\"$undefined\",\"nonce\":\"$undefined\"}]],[\"$\",\"html\",null,{\"lang\":\"ro\",\"suppressHydrationWarning\":true,\"className\":\"__variable_246ccd __variable_c29908 h-full antialiased\",\"children\":[\"$\",\"body\",null,{\"className\":\"min-h-full flex flex-col overscroll-none\",\"children\":[[\"$\",\"$L2\",null,{\"attribute\":\"class\",\"defaultTheme\":\"system\",\"enableSystem\":true,\"disableTransitionOnChange\":true,\"children\":[\"$\",\"$L3\",null,{\"children\":[\"$\",\"$L4\",null,{\"parallelRouterKey\":\"children\",\"error\":\"$undefined\",\"errorStyles\":\"$undefined\",\"errorScripts\":\"$undefined\",\"template\":[\"$\",\"$L5\",null,{}],\"templateStyles\":\"$undefined\",\"templateScripts\":\"$undefined\",\"notFound\":\"$undefined\",\"forbidden\":\"$undefined\",\"unauthorized\":\"$undefined\"}]}]}],[\"$\",\"$L6\",null,{}]]}]}]]}],{\"children\":[[\"$\",\"$1\",\"c\",{\"children\":[null,[\"$\",\"$L4\",null,{\"parallelRouterKey\":\"children\",\"error\":\"$undefined\",\"errorStyles\":\"$undefined\",\"errorScripts\":\"$undefined\",\"template\":[\"$\",\"$L5\",null,{}],\"templateStyles\":\"$undefined\",\"templateScripts\":\"$undefined\",\"notFound\":\"$undefined\",\"forbidden\":\"$undefined\",\"unauthorized\":\"$undefined\"}]]}],{\"children\":[[\"$\",\"$1\",\"c\",{\"children\":[[[\"$\",\"title\",null,{\"children\":\"404: This page could not be found.\"}],[\"$\",\"div\",null,{\"style\":{\"fontFamily\":\"system-ui,\\\"Segoe UI\\\",Roboto,Helvetica,Arial,sans-serif,\\\"Apple Color Emoji\\\",\\\"Segoe UI Emoji\\\"\",\"height\":\"100vh\",\"textAlign\":\"center\",\"display\":\"flex\",\"flexDirection\":\"column\",\"alignItems\":\"center\",\"justifyContent\":\"center\"},\"children\":[\"$\",\"div\",null,{\"children\":[[\"$\",\"style\",null,{\"dangerouslySetInnerHTML\":{\"__html\":\"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}\"}}],[\"$\",\"h1\",null,{\"className\":\"next-error-h1\",\"style\":{\"display\":\"inline-block\",\"margin\":\"0 20px 0 0\",\"padding\":\"0 23px 0 0\",\"fontSize\":24,\"fontWeight\":500,\"verticalAlign\":\"top\",\"lineHeight\":\"49px\"},\"children\":404}],[\"$\",\"div\",null,{\"style\":{\"display\":\"inline-block\"},\"children\":[\"$\",\"h2\",null,{\"style\":{\"fontSize\":14,\"fontWeight\":400,\"lineHeight\":\"49px\",\"margin\":0},\"children\":\"This page could not be found.\"}]}]]}]}]],null,[\"$\",\"$L7\",null,{\"children\":[\"$\",\"$8\",null,{\"name\":\"Next.MetadataOutlet\",\"children\":\"$@9\"}]}]]}],{},null,false,null]},null,false,\"$a\"]},null,false,null],[\"$\",\"$1\",\"h\",{\"children\":[[\"$\",\"meta\",null,{\"name\":\"robots\",\"content\":\"noindex\"}],[\"$\",\"$Lb\",null,{\"children\":\"$Lc\"}],[\"$\",\"div\",null,{\"hidden\":true,\"children\":[\"$\",\"$Ld\",null,{\"children\":[\"$\",\"$8\",null,{\"name\":\"Next.Metadata\",\"children\":\"$Le\"}]}]}],[\"$\",\"meta\",null,{\"name\":\"next-size-adjust\",\"content\":\"\"}]]}],false]],\"m\":\"$undefined\",\"G\":[\"$f\",[]],\"S\":true,\"h\":null,\"r\":\"$undefined\",\"s\":\"$undefined\",\"a\":\"$undefined\",\"l\":\"$undefined\",\"p\":\"$undefined\",\"d\":\"$undefined\",\"b\":\"0WOlzqy4CsZ_r76w9-qKO\"}\na:C\nc:[[\"$\",\"meta\",\"0\",{\"charSet\":\"utf-8\"}],[\"$\",\"meta\",\"1\",{\"name\":\"viewport\",\"content\":\"width=device-width, initial-scale=1, viewport-fit=cover\"}],[\"$\",\"meta\",\"2\",{\"name\":\"theme-color\",\"content\":\"#171717\"}],[\"$\",\"meta\",\"3\",{\"name\":\"color-scheme\",\"content\":\"light dark\"}]]\n10:I[6869,[],\"IconMark\"]\n9:null\ne:[[\"$\",\"title\",\"0\",{\"children\":\"UndePescuim.ro\"}],[\"$\",\"meta\",\"1\",{\"name\":\"description\",\"content\":\"Harta apelor de pescuit contractate din România — contracted fishing waters in Romania\"}],[\"$\",\"link\",\"2\",{\"rel\":\"manifest\",\"href\":\"/manifest.webmanifest\",\"crossOrigin\":\"$undefined\"}],[\"$\",\"meta\",\"3\",{\"name\":\"mobile-web-app-capable\",\"content\":\"yes\"}],[\"$\",\"meta\",\"4\",{\"name\":\"apple-mobile-web-app-title\",\"content\":\"UndePescuim\"}],[\"$\",\"meta\",\"5\",{\"name\":\"apple-mobile-web-app-status-bar-style\",\"content\":\"default\"}],[\"$\",\"link\",\"6\",{\"rel\":\"icon\",\"href\":\"/favicon.ico?603d046c9a6fdfbb\",\"type\":\"image/x-icon\",\"sizes\":\"16x16\"}],[\"$\",\"link\",\"7\",{\"rel\":\"apple-touch-icon\",\"href\":\"/icons/apple-touch-icon-180x180.png\",\"sizes\":\"180x180\",\"type\":\"image/png\"}],[\"$\",\"$L10\",\"8\",{}]]\n"])</script></body></html>

```
`curl --http1.1 -sS -L -D - --max-time 30 https://unde-pescuim.ro/manifest.webmanifest` -> exit 0
```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 166230
Cache-Control: public, max-age=0, must-revalidate
Content-Disposition: inline; filename="manifest.webmanifest"
Content-Length: 485
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: application/manifest+json; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "c8ac12cabeb85fa8d8beb395b7776024"
Last-Modified: Sun, 23 Aug 2026 11:46:57 GMT
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Matched-Path: /manifest.webmanifest
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::v2xvn-1787651848750-883bc0e1d4bd

{"name":"UndePescuim.ro","short_name":"UndePescuim.ro","description":"Harta apelor de pescuit din România — Romanian fishing waters map","start_url":"/","scope":"/","display":"standalone","background_color":"#ffffff","theme_color":"#171717","icons":[{"src":"/icons/icon-192.png","sizes":"192x192","type":"image/png"},{"src":"/icons/icon-512.png","sizes":"512x512","type":"image/png"},{"src":"/icons/icon-512-maskable.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]}

```
`curl --http1.1 -sS -L -D - --max-time 30 https://unde-pescuim.ro/data/waters.json` -> exit 0
```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Age: 166230
Cache-Control: public, max-age=86400
Content-Disposition: inline; filename="waters.json"
Content-Length: 10599467
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Content-Type: application/json; charset=utf-8
Date: Tue, 25 Aug 2026 09:57:28 GMT
Etag: "b100e1c8df76beb7f14e1a9d682461b2"
Last-Modified: Sun, 23 Aug 2026 11:46:58 GMT
Permissions-Policy: camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Referrer-Policy: strict-origin-when-cross-origin
Server: Vercel
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Matched-Path: /data/waters.json
X-Vercel-Cache: HIT
X-Vercel-Id: fra1::lfdnv-1787651848866-c6a9c5417b77

[
 {
  "slug": "jrlgyh2h",
  "name": "Acumulare Agrement",
  "judet": "Bacău",
  "type": "ape",
  "subtype": "lac",
  "limite": "Bacău",
  "dimensiune": "50 ha",
  "pescuit_interzis": false,
  "referinta": "Lista habitatelor piscicole naturale contractate de către asociațiile de pescari recreativi prin contracte pentru utilizarea resurselor acvatice vii în scop recreativ, la data 01.02.2024",
  "coordinates": [
   26.92668096762032,
   46.56464089079679
  ],
  "driving": [
   26.92668096762032,
   46.56464089079679
  ],
  "bbox": [
   26.923014,
   46.55703,
   26.931644,
   46.57411
  ],
  "asociatie": {
   "name": "AJVPS BACĂU",
   "name_long": "Asociația Județeană a Vănătorilor și Pescarilor Sportivi Bacău",
   "slug": "ajvps-bacau",
   "adresa": "str. Mihai Viteazu, nr. 4, Bacău",
   "siteUrl": "https://ajvpsbc.ro/",
   "permitIssuer": "asociatie"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      26.9236,
      46.57399
     ],
     [
      26.92576,
      46.57223
     ],
     [
      26.93162,
      46.55925
     ],
     [
      26.9277,
      46.55705
     ],
     [
      26.92445,
      46.56179
     ],
     [
      26.9236,
      46.57399
     ]
    ],
    [
     [
      26.92652,
      46.56361
     ],
     [
      26.92775,
      46.56461
     ],
     [
      26.9246,
      46.56382
     ],
     [
      26.9257,
      46.56025
     ],
     [
      26.9283,
      46.56012
     ],
     [
      26.92904,
      46.56155
     ],
     [
      26.92652,
      46.56361
     ]
    ],
    [
     [
      26.92685,
      46.55933
     ],
     [
      26.92645,
      46.56015
     ],
     [
      26.926,
      46.55972
     ],
     [
      26.92685,
      46.55933
     ]
    ]
   ]
  },
  "source": "hotosm",
  "source_detail": "bbox_fix:lake:Lacul de acumulare Bacău I",
  "locality": "Bacău",
  "areaHa": 44.92
 },
 {
  "slug": "ldcmx0lr",
  "name": "Acumulare Bacău II",
  "judet": "Bacău",
  "type": "ape",
  "subtype": "lac",
  "limite": "Bacău",
  "dimensiune": "202 ha",
  "pescuit_interzis": false,
  "referinta": "Lista habitatelor piscicole naturale contractate de către asociațiile de pescari recreativi prin contracte pentru utilizarea resurselor acvatice vii în scop recreativ, la data 26.04.2024",
  "coordinates": [
   26.9214495990457,
   46.58499476993064
  ],
  "driving": [
   26.9214495990457,
   46.58499476993064
  ],
  "bbox": [
   26.9147183,
   46.5739457,
   26.9273242,
   46.5945173
  ],
  "asociatie": {
   "name": "Centrul Regional de Ecologie Bacău",
   "name_long": "Centrul Regional de Ecologie Bacău",
   "slug": "centrul-regional-de-ecologie-bacau",
   "siteUrl": "https://naturabacau.ro/pescuit-recreativ/",
   "permitIssuer": "asociatie"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      26.91472,
      46.58822
     ],
     [
      26.91764,
      46.58463
     ],
     [
      26.92046,
      46.57468
     ],
     [
      26.92412,
      46.57422
     ],
     [
      26.92732,
      46.57693
     ],
     [
      26.92614,
      46.59284
     ],
     [
      26.91572,
      46.59443
     ],
     [
      26.91726,
      46.58944
     ],
     [
      26.91472,
      46.58822
     ]
    ]
   ]
  },
  "locality": "Bacău",
  "areaHa": 143.57
 },
 {
  "slug": "uqvbagnh",
  "name": "Acumulare Berești",
  "judet": "Bacău",
  "type": "ape",
  "subtype": "lac",
  "limite": "Sascut - Berești",
  "dimensiune": "1800 ha",
  "pescuit_interzis": false,
  "referinta": "Lista habitatelor piscicole naturale contractate de către asociațiile de pescari recreativi prin contracte pentru utilizarea resurselor acvatice vii în scop recreativ, la data 01.02.2024",
  "coordinates": [
   27.13474564867682,
   46.24159593807913
  ],
  "driving": [
   27.13474564867682,
   46.24159593807913
  ],
  "bbox": [
   27.08102,
   46.185418,
   27.195761,
   46.289334
  ],
  "asociatie": {
   "name": "AJVPS BACĂU",
   "name_long": "Asociația Județeană a Vănătorilor și Pescarilor Sportivi Bacău",
   "slug": "ajvps-bacau",
   "adresa": "str. Mihai Viteazu, nr. 4, Bacău",
   "siteUrl": "https://ajvpsbc.ro/",
   "permitIssuer": "asociatie"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      27.08102,
      46.28664
     ],
     [
      27.08852,
      46.28932
     ],
     [
      27.08845,
      46.28751
     ],
     [
      27.0927,
      46.28667
     ],
     [
      27.09524,
      46.2886
     ],
     [
      27.09985,
      46.28848
     ],
     [
      27.10243,
      46.28445
     ],
     [
      27.11218,
      46.27681
     ],
     [
      27.11409,
      46.27167
     ],
     [
      27.1146,
      46.2621
     ],
     [
      27.11997,
      46.25754
     ],
     [
      27.13044,
      46.25771
     ],
     [
      27.14243,
      46.25116
     ],
     [
      27.14592,
      46.2422
     ],
     [
      27.15172,
      46.23393
     ],
     [
      27.16662,
      46.22308
     ],
     [
      27.16805,
      46.21639
     ],
     [
      27.17229,
      46.21137
     ],
     [
      27.18211,
      46.20469
     ],
     [
      27.18578,
      46.1986
     ],
     [
      27.19426,
      46.19308
     ],
     [
      27.19558,
      46.19047
     ],
     [
      27.18714,
      46.18545
     ],
     [
      27.17746,
      46.18845
     ],
     [
      27.11321,
      46.24822
     ],
     [
      27.10483,
      46.25887
     ],
     [
      27.10668,
      46.26541
     ],
     [
      27.10231,
      46.26421
     ],
     [
      27.10148,
      46.26532
     ],
     [
      27.10551,
      46.26719
     ],
     [
      27.10469,
      46.26916
     ],
     [
      27.09814,
      46.27083
     ],
     [
      27.09391,
      46.2741
     ],
     [
      27.09898,
      46.27346
     ],
     [
      27.10005,
      46.27381
     ],
     [
      27.09845,
      46.27572
     ],
     [
      27.10252,
      46.27662
     ],
     [
      27.10034,
      46.27678
     ],
     [
      27.1003,
      46.27818
     ],
     [
      27.10232,
      46.27815
     ],
     [
      27.1008,
      46.27963
     ],
     [
      27.09554,
      46.28216
     ],
     [
      27.09948,
      46.28191
     ],
     [
      27.09777,
      46.28322
     ],
     [
      27.08797,
      46.28207
     ],
     [
      27.08102,
      46.28664
     ]
    ]
   ]
  },
  "source": "hotosm",
  "source_detail": "bbox_fix:lake:Lacul Berești",
  "locality": "Sascut",
  "areaHa": 1755.04
 },
 {
  "slug": "hdqe290r",
  "name": "Acumulare Canciu",
  "judet": "Alba",
  "type": "ape",
  "subtype": "lac",
  "limite": "Artificial",
  "dimensiune": "12 ha",
  "pescuit_interzis": false,
  "referinta": "LISTA HABITATELOR PISCICOLE NATURALE DIN APELE DE MUNTE și rămase în administrarea directă a regiei prin Protocolul nr. 12935/LAV/17.09.2013 administrate de RNP - ROMSILVA în baza Protocolului nr. 10711/19.04.2010",
  "coordinates": [
   23.5058574271456,
   45.66568440675325
  ],
  "driving": [
   23.5058574271456,
   45.66568440675325
  ],
  "bbox": [
   23.497787,
   45.661088,
   23.510109,
   45.668139
  ],
  "asociatie": {
   "name": "Direcția Silvică Alba",
   "name_long": "Direcția Silvică Alba",
   "slug": "directia-silvica-alba",
   "telefon": "0258812138",
   "adresa": "Strada Basarabiei 9, Alba Iulia",
   "siteUrl": "http://alba.rosilva.ro/",
   "permitIssuer": "romsilva"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      23.51011,
      45.66802
     ],
     [
      23.49875,
      45.66261
     ],
     [
      23.49779,
      45.66114
     ],
     [
      23.5082,
      45.66581
     ],
     [
      23.51011,
      45.66802
     ]
    ]
   ]
  },
  "source": "hotosm",
  "source_detail": "bbox_fix:lake:Canciu",
  "locality": "Cugir",
  "areaHa": 11.08
 },
 {
  "slug": "lpfud98o",
  "name": "Acumulare Căpâlna",
  "judet": "Alba",
  "type": "ape",
  "subtype": "lac",
  "limite": "Artificial",
  "dimensiune": "37 ha",
  "pescuit_interzis": false,
  "referinta": "LISTA HABITATELOR PISCICOLE NATURALE DIN APELE DE MUNTE și rămase în administrarea directă a regiei prin Protocolul nr. 12935/LAV/17.09.2013 administrate de RNP - ROMSILVA în baza Protocolului nr. 10711/19.04.2010",
  "coordinates": [
   23.61508174561434,
   45.8132772722446
  ],
  "driving": [
   23.61508174561434,
   45.8132772722446
  ],
  "bbox": [
   23.607269,
   45.810038,
   23.621408,
   45.821897
  ],
  "asociatie": {
   "name": "Direcția Silvică Alba",
   "name_long": "Direcția Silvică Alba",
   "slug": "directia-silvica-alba",
   "telefon": "0258812138",
   "adresa": "Strada Basarabiei 9, Alba Iulia",
   "siteUrl": "http://alba.rosilva.ro/",
   "permitIssuer": "romsilva"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      23.61139,
      45.82154
     ],
     [
      23.60727,
      45.8188
     ],
     [
      23.61125,
      45.81641
     ],
     [
      23.61267,
      45.81176
     ],
     [
      23.61566,
      45.81132
     ],
     [
      23.61787,
      45.81318
     ],
     [
      23.62034,
      45.81004
     ],
     [
      23.62141,
      45.81056
     ],
     [
      23.61848,
      45.81351
     ],
     [
      23.61494,
      45.81242
     ],
     [
      23.61315,
      45.8136
     ],
     [
      23.6125,
      45.81718
     ],
     [
      23.60882,
      45.81895
     ],
     [
      23.61139,
      45.82154
     ]
    ]
   ]
  },
  "source": "hotosm",
  "source_detail": "bbox_fix:lake-unnamed:",
  "locality": "Săsciori",
  "areaHa": 17.84
 },
 {
  "slug": "eovhns40",
  "name": "Acumulare Galbeni",
  "judet": "Bacău",
  "type": "ape",
  "subtype": "lac",
  "limite": "Nicolae Bălcescu-Galbeni",
  "dimensiune": "250 ha",
  "pescuit_interzis": false,
  "referinta": "Lista habitatelor piscicole naturale contractate de către asociațiile de pescari recreativi prin contracte pentru utilizarea resurselor acvatice vii în scop recreativ, la data 26.04.2024",
  "coordinates": [
   26.962568762711204,
   46.479698035539066
  ],
  "driving": [
   26.962568762711204,
   46.479698035539066
  ],
  "bbox": [
   26.9466581,
   46.454334,
   26.98162510689,
   46.50542527519
  ],
  "asociatie": {
   "name": "Centrul Regional de Ecologie Bacău",
   "name_long": "Centrul Regional de Ecologie Bacău",
   "slug": "centrul-regional-de-ecologie-bacau",
   "siteUrl": "https://naturabacau.ro/pescuit-recreativ/",
   "permitIssuer": "asociatie"
  },
  "geometry": {
   "type": "Polygon",
   "coordinates": [
    [
     [
      26.94666,
      46.45433
     ],
     [
      26.98163,
      46.45433
     ],
     [
      26.98163,
      46.50543
     ],
     [
      26.94666,
      46.50543
     ],
     [
      26.94666,
      46.45433
     ]
    ]
   ]
  },
  "locality": "Tamași",
  "areaHa": 1524.89
 },
 {
  "slug": "hvy996q6",
  "name": "Acumulare Gârleni",
  "judet": "Bacău",
  "type": "a
[body truncated at 12000 chars]

```
### TLS certificate and errors
`openssl s_client -connect unde-pescuim.ro:443 -servername unde-pescuim.ro -showcerts -verify_return_error` -> exit 0
```
CONNECTED(00000003)
---
Certificate chain
 0 s:CN = unde-pescuim.ro
   i:C = US, O = Let's Encrypt, CN = YR2
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Aug 24 09:31:48 2026 GMT; NotAfter: Nov 22 09:31:47 2026 GMT
-----BEGIN CERTIFICATE-----
MIIE+jCCA+KgAwIBAgISBfW0cvCEHH4tPS4ZavJ5uL6tMA0GCSqGSIb3DQEBCwUA
MDMxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQwwCgYDVQQD
EwNZUjIwHhcNMjYwODI0MDkzMTQ4WhcNMjYxMTIyMDkzMTQ3WjAaMRgwFgYDVQQD
Ew91bmRlLXBlc2N1aW0ucm8wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
AQCtL8v8PW3DCo/yPmCSaHjgRAWKNto8dn8qj9PMwBnjQ40D6u38tdmq6UU4AOXv
TJ0INBhFIqfDcTjpVXii9lhfN/aos0sbQdnmWGlGFu5xzR/m1wWmBK1O84n9+p2z
Gld2U5TKEMcvLe0Uy7du5pWnlTdGXtEAqk7sZQQ1vzQ8NdFu1IcKCj+HsQDDjkAU
mOuavqcT9/Wh6ypM179Bi8a6N28+N/6RKWC+YjZjTSxBo9Q4CzY+7P5VHA8PaW+v
7lwUi/1PEo9BAlyQ8997SWfHsDGXyIzckZzjrN4ajovOChSXVPfvX+KwjPdfDM+J
scBWTpGSEJx8th9n3GAZaxWRAgMBAAGjggIfMIICGzAOBgNVHQ8BAf8EBAMCBaAw
EwYDVR0lBAwwCgYIKwYBBQUHAwEwDAYDVR0TAQH/BAIwADAdBgNVHQ4EFgQU5xtS
y3Yhd4lVURnrcvM1JkXh5MkwHwYDVR0jBBgwFoAUQBUtJnntMiCe35pyHdYyH4EM
gQwwMwYIKwYBBQUHAQEEJzAlMCMGCCsGAQUFBzAChhdodHRwOi8veXIyLmkubGVu
Y3Iub3JnLzAaBgNVHREEEzARgg91bmRlLXBlc2N1aW0ucm8wEwYDVR0gBAwwCjAI
BgZngQwBAgEwLgYDVR0fBCcwJTAjoCGgH4YdaHR0cDovL3lyMi5jLmxlbmNyLm9y
Zy80Ni5jcmwwggEOBgorBgEEAdZ5AgQCBIH/BIH8APoAdwDCMX5XRRmjRe5/ON6y
kEHrx8IhWiK/f9W1rXaa2Q5SzQAAAaAzUi1rAAAEAwBIMEYCIQCKdunedi+CXHz7
/LIMqQusYEyNvjcLj/JhWA1tmYmQ0gIhAOKrlfngeZLvFV417ziwTz3UbSkFe3Gf
9Cr8h/bih/A2AH8AbP5QGUOoXqkWvFLRM+TcyR7xQRx9JYQg0XOAnhgY6zoAAAGg
M1IucgAIAAAFACU4ItsEAwBIMEYCIQCI6MKJt8TaHdkOj1XL6mus8awSesvKjWTz
S91PXqioTgIhAP/ZjmMjjGgfAJMDsFHpNtD6CplCaB6HoOrc0qb1M0v8MA0GCSqG
SIb3DQEBCwUAA4IBAQCt6RccdLvUgBQIHVfPXJl8gaJmgIUDWsHom8njzDdnihjp
rZ9Y8KOr5RdPDF2UBd/pq8YSXIwxBuZMlw7kDfIHIrC5IxawFvnM81wnHJ2rr27g
M63iNp+uX+TQklp8OOkAczOLCWcKusiTC6lix69iy19Rgi3nDbN1YHP+YEGtQlq5
XyOpFa7fZKY33YbcsXkZ2nssYNVayaIUuZNLCOqR+i9pQdj9UwJud7slfW+ic+mI
/FXgH18OR8kvVWo2sqvanCWAPULfJTrNCG0WdstFipBcYcDhixG2Zr1zn12MREte
YL3M11gGGC7bbVmGl5Kn+CIvoiOtEfFIq3u2y/5f
-----END CERTIFICATE-----
 1 s:C = US, O = Let's Encrypt, CN = YR2
   i:C = US, O = ISRG, CN = Root YR
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Sep  3 00:00:00 2025 GMT; NotAfter: Sep  2 23:59:59 2028 GMT
-----BEGIN CERTIFICATE-----
MIIE2jCCAsKgAwIBAgIQTr0klH4k05SALYSlL9WzGTANBgkqhkiG9w0BAQsFADAu
MQswCQYDVQQGEwJVUzENMAsGA1UEChMESVNSRzEQMA4GA1UEAxMHUm9vdCBZUjAe
Fw0yNTA5MDMwMDAwMDBaFw0yODA5MDIyMzU5NTlaMDMxCzAJBgNVBAYTAlVTMRYw
FAYDVQQKEw1MZXQncyBFbmNyeXB0MQwwCgYDVQQDEwNZUjIwggEiMA0GCSqGSIb3
DQEBAQUAA4IBDwAwggEKAoIBAQDZ0LxwBppqh84luqMerV/eeL/fXQ7mLQQv1Lnp
WKZbyvGpx6wh6AfnslAnF6ewTkcHA+gSOoBvm3Dfm06AuGiF+KRut4fAcowqnAQQ
CW98+QPP/eOv/wug7Iyk4NkOxf2I6g2f55T6nJoOTLFcukeRq80JGQEYan+dPFr9
OGUgQK2hGKgNkW87pappsOAuUJcroYhRt5uUis4qaZireiseu32gzDJNBAiKtsvd
6HX4v25bpkRNcS/B/Gtc9kVbUpD+2PLPxdei3Tim55k4tfAEXwD2qyiPTxrTNq6l
N+AMr5g2c1dNqkOTwjxeV6L5lpP1rGiYvLnRaPlOqyZRPW+5AgMBAAGjge4wgesw
DgYDVR0PAQH/BAQDAgGGMBMGA1UdJQQMMAoGCCsGAQUFBwMBMBIGA1UdEwEB/wQI
MAYBAf8CAQAwHQYDVR0OBBYEFEAVLSZ57TIgnt+ach3WMh+BDIEMMB8GA1UdIwQY
MBaAFN7nW2DQIm1AKH0/DQH+pLVStFGUMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEF
BQcwAoYWaHR0cDovL3lyLmkubGVuY3Iub3JnLzATBgNVHSAEDDAKMAgGBmeBDAEC
ATAnBgNVHR8EIDAeMBygGqAYhhZodHRwOi8veXIuYy5sZW5jci5vcmcvMA0GCSqG
SIb3DQEBCwUAA4ICAQB0ZUQWZ9/Yn9COEpo+JfecMnB0h0vwDm/M66IqXqw3LoaL
mx9lZvRTeDIS67PUeI3yCA2W6PKRD0/FE/G57lOmS+Xy5AaaL00ICGOqjNcCaMWW
8o8nevHOd4i4lqgtznE/28QwlcdJyF8yBiWHpnyjhEpmNWJURgOCOg2xpwRMBCsj
MScqYPtOhBeuYQvSwAEeTML2Ukh6uGuX4E14q65Ja8cdjF5bAldnP1eE4FBaAwsZ
G2fOqqrKV03Y85Nw2btedP1AtliQuJZs/Jo/gXxXdc7LrH3McgnpnbTiAncX7yES
hP6kzQejllqMCIt52HOjxDGWafS7Xw+DKwqmH+Eqy8dcbOuag/1AYlQoKNVK3F5q
Hh6tEDiMqQcLIibGKteE6iHo4A/bIScbzrhXUYuism42ZYzmc48FMVIH3qy4L84E
TdAH2gtxw0PAhvRVXp8HP7wfngpzsN/8xOTpeRSbM4+Qbc56G6+Bifmv6sk1ieQb
NA3wJdl4DDUuQSV8hBgx6zoI1ZSGORprDFux7c6rhc77QZMSRrEgomBeklervEve
86ylWmZ3WWHV6RLMi8xNvjd71r4EPIGgY7BZU/VPBkq+uA7Gb6mbJnFgV43uh3xy
LRFgxIAphIukwTGSMZZR+AI+Qnp0BYTWovHXozOf3H8r6hozEoT02JHn0AeTfA==
-----END CERTIFICATE-----
 2 s:C = US, O = ISRG, CN = Root YR
   i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
   a:PKEY: rsaEncryption, 4096 (bit); sigalg: RSA-SHA256
   v:NotBefore: May 13 00:00:00 2026 GMT; NotAfter: Sep  2 23:59:59 2032 GMT
-----BEGIN CERTIFICATE-----
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
-----END CERTIFICATE-----
---
Server certificate
subject=CN = unde-pescuim.ro
issuer=C = US, O = Let's Encrypt, CN = YR2
---
No client certificate CA names sent
Peer signing digest: SHA256
Peer signature type: RSA-PSS
Server Temp Key: X25519, 253 bits
---
SSL handshake has read 4606 bytes and written 381 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_128_GCM_SHA256
Server public key is 2048 bit
Secure Renegotiation IS NOT supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
Early data was not sent
Verify return code: 0 (ok)
---
---
Post-Handshake New Session Ticket arrived:
SSL-Session:
    Protocol  : TLSv1.3
    Cipher    : TLS_AES_128_GCM_SHA256
    Session-ID: 5EF82B47183CB7E2A69E9DBE517B28F9E08900EE5C5E2D8E6AFEC58D412ECE26
    Session-ID-ctx: 
    Resumption PSK: 29A97D68BC8CB67CB4EC71C927365D9B888A1770440103D6AAAFF1039C472E48
    PSK identity: None
    PSK identity hint: None
    SRP username: None
    TLS session ticket lifetime hint: 604800 (seconds)
    TLS session ticket:
    0000 - 64 88 d0 4e 12 91 fc d1-72 e0 da 7e 14 0e 8e 5a   d..N....r..~...Z
    0010 - c6 02 7a 0c f7 37 97 ac-d8 9c ee 54 66 e6 f8 e9   ..z..7.....Tf...
    0020 - 5a 4f 19 cb 72 bb 9f 3f-18 8e 25 bf 13 61 78 fe   ZO..r..?..%..ax.
    0030 - 0f bd cf 72 98 86 24 dd-00 25 a7 20 cc 6a e4 17   ...r..$..%. .j..
    0040 - 7e 78 aa 3b 10 d0 1e e0-3e 59 88 da 1d 00 38 06   ~x.;....>Y....8.
    0050 - a6 ad a0 dc 30 f0 66 21-49 a1 36 d9 30 f2 9b 7b   ....0.f!I.6.0..{
    0060 - 75 c8 a5 ad 10 29 8a d3-2e                        u....)...

    Start Time: 1787651849
    Timeout   : 7200 (sec)
    Verify return code: 0 (ok)
    Extended master secret: no
    Max Early Data: 0
---
read R BLOCK
depth=3 C = US, O = Internet Security Research Group, CN = ISRG Root X1
verify return:1
depth=2 C = US, O = ISRG, CN = Root YR
verify return:1
depth=1 C = US, O = Let's Encrypt, CN = YR2
verify return:1
depth=0 CN = unde-pescuim.ro
verify return:1
DONE

```
`openssl s_client -connect www.unde-pescuim.ro:443 -servername www.unde-pescuim.ro -showcerts -verify_return_error` -> exit 0
```
CONNECTED(00000003)
---
Certificate chain
 0 s:CN = www.unde-pescuim.ro
   i:C = US, O = Let's Encrypt, CN = YR1
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Aug 24 09:31:49 2026 GMT; NotAfter: Nov 22 09:31:48 2026 GMT
-----BEGIN CERTIFICATE-----
MIIFATCCA+mgAwIBAgISBtjQnEs7ymKaFSOe7UcjLMkkMA0GCSqGSIb3DQEBCwUA
MDMxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQwwCgYDVQQD
EwNZUjEwHhcNMjYwODI0MDkzMTQ5WhcNMjYxMTIyMDkzMTQ4WjAeMRwwGgYDVQQD
ExN3d3cudW5kZS1wZXNjdWltLnJvMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEArpFwiwuSrL6HVHwBHJfU6DCEl5+rAczPq6Mh/mgZhffoTLTtMdNPlKCG
V5XpRkT81hO8hF6uiCh7F70ZsrtPJXlthR0pTIt7iSn70FgJmEECStmYISLTtn1v
a5p9ibvbGAYThHL8BeeoU0IOLMF7JO+SWKUyoZ0FcOAUG0oRM3gEE6294fvpyapo
nAVv/9uEYUcSzaZd9FTZOiyH8OXRitrrcJ409I22CM52z3yg+QoHTpiioqL82/yM
SFcXr5YKbTqPi04H+I7ZaDLgW2eu5HdX/Htz64lJQMda8PRGnKxjJRf0LX4OmxTK
9ZUuUa772z6Lw35huzikMnfPnIjWBwIDAQABo4ICIjCCAh4wDgYDVR0PAQH/BAQD
AgWgMBMGA1UdJQQMMAoGCCsGAQUFBwMBMAwGA1UdEwEB/wQCMAAwHQYDVR0OBBYE
FC6hYNmwqPTYGntnT1PHAKRqgRz+MB8GA1UdIwQYMBaAFB8vNb5GFILNQLGueSxV
ePr31Gj7MDMGCCsGAQUFBwEBBCcwJTAjBggrBgEFBQcwAoYXaHR0cDovL3lyMS5p
LmxlbmNyLm9yZy8wHgYDVR0RBBcwFYITd3d3LnVuZGUtcGVzY3VpbS5ybzATBgNV
HSAEDDAKMAgGBmeBDAECATAuBgNVHR8EJzAlMCOgIaAfhh1odHRwOi8veXIxLmMu
bGVuY3Iub3JnLzM3LmNybDCCAQ0GCisGAQQB1nkCBAIEgf4EgfsA+QB/AEavhj07
PuWfpXfeqCRdNrDZ7SKiI/Rhd0EilFLulVBfAAABoDNSMKAACAAABQAbwXPmBAMA
SDBGAiEAmi77FrRarvREzg1YhSdEuZA/LStN5plpT/Yi0qG6vh4CIQC10FuODt1d
f8XUGcs2FCPxHuPusfg1tJN2POD6AQZNXAB2AK9niDtXsE7dj6bZfvYuqOuBCsdx
YPAkXlXWDC/nhYc6AAABoDNSMK0AAAQDAEcwRQIhAPIrxQyGVCqWE1tIwPftlU0V
8K7uS+8sjWRV/BL0L9CLAiB93eQRnMyor50myruzEujvoch4r+IFjpMwbNfnXqcO
vzANBgkqhkiG9w0BAQsFAAOCAQEAEtimyjdJA55EHLZr1mH1wUxWq7e/hrcBw2zd
RNlDHkMsocaVUYXyqXjzaKx0Mra73co9BjbwhcLz4FlgSi1kj1Q+zYq5/8wEZrwE
WGQot5GpsmULsPvWsIs+0hLeO7qTUcEOfz6m96uPQoiR8+hIsCdPyuICh0Bw0p0i
LfAlZh0ExAtpdG7Wg+nD+VXMR/NDjHDZfSPbUXtIqhjRmXH6/DF1nxbEl/M+zJEA
YgOoNSeNgMrdRE74aCGQr4RUhY+Dviyobo9DiO3g0ygN4bO3o5SrtDYRWz3qKgex
o7QrwEYgDcUuTT9wT/LJM2Nrf66Eig6KcxaDG+OnFeXtEyV7Ow==
-----END CERTIFICATE-----
 1 s:C = US, O = Let's Encrypt, CN = YR1
   i:C = US, O = ISRG, CN = Root YR
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Sep  3 00:00:00 2025 GMT; NotAfter: Sep  2 23:59:59 2028 GMT
-----BEGIN CERTIFICATE-----
MIIE2zCCAsOgAwIBAgIRAKICU/FfJpHAXcHOE7m8yk4wDQYJKoZIhvcNAQELBQAw
LjELMAkGA1UEBhMCVVMxDTALBgNVBAoTBElTUkcxEDAOBgNVBAMTB1Jvb3QgWVIw
HhcNMjUwOTAzMDAwMDAwWhcNMjgwOTAyMjM1OTU5WjAzMQswCQYDVQQGEwJVUzEW
MBQGA1UEChMNTGV0J3MgRW5jcnlwdDEMMAoGA1UEAxMDWVIxMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoVi8X2xCYgMXvJxNPKp/oF13UMgmPABB07VC
LNDtoXmt9luEZNJSBV10VyT1Pz6LD8Zq1d2gc43WNl1AdRrj4sEnazbOiz0nPpmG
Bp2hui49oZtDIY6wdKeZAi5BbNU20CH6RSBBMLSQ9cXrH8dxdv4PAJ45ssGML68U
SE3BsjC2a6cAN9L5CgXVIQi5tfNiTPoFZZ3S0OlXqLmmtdV95udWAb5b6e/F49Di
CsH0Y00Ag72BVIb1hzynmKe+X0mERBTtsb3BwmpV9ipeBjMLoR/D9cHxHQCWoi5l
TmXwY015J5rGelz1nZjJuxc2kioaX29XJBnhMkP531rSdG5uMwIDAQABo4HuMIHr
MA4GA1UdDwEB/wQEAwIBhjATBgNVHSUEDDAKBggrBgEFBQcDATASBgNVHRMBAf8E
CDAGAQH/AgEAMB0GA1UdDgQWBBQfLzW+RhSCzUCxrnksVXj699Ro+zAfBgNVHSME
GDAWgBTe51tg0CJtQCh9Pw0B/qS1UrRRlDAyBggrBgEFBQcBAQQmMCQwIgYIKwYB
BQUHMAKGFmh0dHA6Ly95ci5pLmxlbmNyLm9yZy8wEwYDVR0gBAwwCjAIBgZngQwB
AgEwJwYDVR0fBCAwHjAcoBqgGIYWaHR0cDovL3lyLmMubGVuY3Iub3JnLzANBgkq
hkiG9w0BAQsFAAOCAgEA0+zvMq3kHig1ddTmmm+RibTr9/RpX7k4buanMMRqbV/y
IvP82zAHN3mvaw+cASuVsdpd0ikjhr4hnhJQLQOzOp2ccKrsdGOAgo0vddeISFAq
EWEV4lmUM3vFF796up+bSgmJ1u6RupDCMxDgF8M3eLvGuj6L0lu3zkQ0KuQLnKxL
tB0oQqn1Idg5CuuGpMvQzk29Pa3D/qHurc0EIM9SxukQuJqq63lxsYyRQFU8yMBO
hq1w5LbfaWNRrz1uklOfI/pYkAb2E2MTZrAMQkBIE2S8Jt1F8gRc96o/xOsrgvSk
a84AisX6xq1lz1Z7jGvrnXc4TMcjxZTjiTaihcYI1JIXZiLtEMSCa5l3cu8YWd6z
dLRQlqRdclVjuQfNHawRJ6GWlkK0QJosivTKwdBw3KxEtzGo8yMHERbsy57gP1UX
HOMcmZYQC0gtyR3SxfenIM/MxC3Ia2Ypab/kQ/CTnlIn2KQ5JUC6NYrGCbhFN9bp
5lKJStEwCUnLpntcrXk5XVDCNv/5RyWpRThkGOV7GetKkQ0qAY8hCzWK6oqnAhDZ
cjlYVdWfqOw3DIOX6EDNBgAqHarRVxyF9QZdOaXSyPJ0ueD2BYJEBgaCGQ8rAaU/
Qc123V5LTXDZW4CcsPBDyhy4v+c8hClAyw/IkJlfBqxB9D+/wvIMHgECZ4ptP6o=
-----END CERTIFICATE-----
 2 s:C = US, O = ISRG, CN = Root YR
   i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
   a:PKEY: rsaEncryption, 4096 (bit); sigalg: RSA-SHA256
   v:NotBefore: May 13 00:00:00 2026 GMT; NotAfter: Sep  2 23:59:59 2032 GMT
-----BEGIN CERTIFICATE-----
MIIF9DCCA9ygAwIBAgIRAPJLbRf52a18scn+p4eCaZ8wDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjYwNTEzMDAwMDAw
WhcNMzIwOTAyMjM1OTU5WjAuMQswCQYDVQQGEwJVUzENMAsGA1UEChMESVNSRzEQ
MA4GA1UEAxMHUm9vdCBZUjCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIB
ANvGJnN78CTJdWL3+eGfsLN5TrNBJs+VH9hRXqRbwxu9sGNiB0BD1fcOxbSUQCJI
M1xE13Db+5Cw1w0s0EBYsvuIP/6joF0w8cuImbgR1OGgYbSQ4OpzI+DG8SGuTlcE
873OCS+kh3srlo6vl43M5OJg4Aeo1sfHp6kTJDoIiFBNJAY+OKfX/FUvYKuhjT+n
o49lmqmupSBI5PkBQiqrEGtWU5uxU/cQWHGu8jSjFBznZqvbNPLMXMLFxCb3WTfr
JBXXjqvWG+v4bjzxjjeAtOlU7qarRDvNOyAuQYLln904M+faKx8hnLCpJ15ZqaEg
cNlY+9MMWcC5yvL2A2j3l9+2buggZX+dOE91zYmIdawTvSZuVvlbRrAlLxIB6pwM
BjneXCjYQ8+3BCCjssbSNpZU3hTcBDdhfAlEDlYr6pEatnMdmDT5BqnKC92bd0Eh
M1fbLHioLccLCuievT8ZkPhZrq7Mii7gNXAcUEAR8+lzYal+9zTg7C5DALyVOeG/
CqfRAMn1KSHCR0NSA6P8tn/mGRlnCct5rtVCLnVySVpU6H1qGg3DgTOuskf8eahT
MiYbI5ezPJmO5ertalskQ1utp74+eDy92PI4ftHKTbq9IWhH4YZKh3WnJEIt+oQv
lYZbY8tpEroKrFB6PFGzrJIDRyts4HqvuH52RFj2zv/BAgMBAAGjgeswgegwDgYD
VR0PAQH/BAQDAgEGMBMGA1UdJQQMMAoGCCsGAQUFBwMBMA8GA1UdEwEB/wQFMAMB
Af8wHQYDVR0OBBYEFN7nW2DQIm1AKH0/DQH+pLVStFGUMB8GA1UdIwQYMBaAFHm0
WeZ7tuXkAXOACIjIGlj26ZtuMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEFBQcwAoYW
aHR0cDovL3gxLmkubGVuY3Iub3JnLzATBgNVHSAEDDAKMAgGBmeBDAECATAnBgNV
HR8EIDAeMBygGqAYhhZodHRwOi8veDEuYy5sZW5jci5vcmcvMA0GCSqGSIb3DQEB
CwUAA4ICAQA8spSI95KKfn2W6GMmDpHBJSPaLbsS3W93cijJCRCYAc1fsJgL1FIL
7C0C9ecPOdcwB2fi0Dk2p94j9iTJCxmt5CFSKLRWwnXT2MMSXexVxqoVB79BdWPx
VXETkVme/qYSAuKVHh5Ps+5BixgmwS1JkjSAc+MfrUbNssVEEnH0aEiAh+rotXAV
JSP/Ye7LJPEwD9DWG72vVWbhAcuOf5OLjz57Ctk7MgQHynZ7+PlHJtajroCaIbtC
r6tcZZaAwUQm+jQyeWdV+2hv9deOYFmKeQyjjcSrN5Nadrw+L9DZJLbA1HqeNvLh
BgqpP0fvJq2N6EtD574N6eMI7uMsJTnji2UDz9el5XLSv9fqJMuDQtYVb2oTNoKp
oUqhxPVC0aq4eG5MESaIdn8b5ZGSSeAJLMHXljEdlNza+ncfkviXk1POLnnFdvx8
/gk6M374WbLWFXw8N141B/Rl/tINGfl1TxOIiqtiMYkL02RSGb1kq34BL9NPP27z
RGMuHGnzS3hFIrRTfKxrzUZ9RzQWzEG3K6fJ3r2nqSltkeytis9DIBoFY9VmVyjL
M71DMi+y1+TRSJVClEMwvA4yL++7q9XZx5r5wBRWB4kQTKH5qyoZnDw7iiuh1lID
yDFx8r7i9vIJU5HS3moZLkYWAOilMaV9N56A9Bgb6dNcHkvg3NoaYA==
-----END CERTIFICATE-----
---
Server certificate
subject=CN = www.unde-pescuim.ro
issuer=C = US, O = Let's Encrypt, CN = YR1
---
No client certificate CA names sent
Peer signing digest: SHA256
Peer signature type: RSA-PSS
Server Temp Key: X25519, 253 bits
---
SSL handshake has read 4614 bytes and written 385 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_128_GCM_SHA256
Server public key is 2048 bit
Secure Renegotiation IS NOT supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
Early data was not sent
Verify return code: 0 (ok)
---
---
Post-Handshake New Session Ticket arrived:
SSL-Session:
    Protocol  : TLSv1.3
    Cipher    : TLS_AES_128_GCM_SHA256
    Session-ID: 15302C5B6AEF8A01C8793F231925F12ADC8853BCAAC6D115700B33F5A7EDF744
    Session-ID-ctx: 
    Resumption PSK: 6B7E3D2C39B8D6C249A43587AC3D0AAFD94D77EBA416E13C626E390012A70C95
    PSK identity: None
    PSK identity hint: None
    SRP username: None
    TLS session ticket lifetime hint: 604800 (seconds)
    TLS session ticket:
    0000 - d2 51 79 69 03 e1 4f ca-5f 1f d0 2f f5 29 79 b4   .Qyi..O._../.)y.
    0010 - 7d 3d 52 05 a8 7b c9 22-9d 87 06 41 30 34 6f 0f   }=R..{."...A04o.
    0020 - e6 49 1c d0 37 45 3d e3-eb 25 12 66 7c 0a 39 ae   .I..7E=..%.f|.9.
    0030 - 9f af f5 73 e9 51 46 34-df 0e 1f c2 9f 44 ca 5e   ...s.QF4.....D.^
    0040 - 52 17 95 3b 84 26 16 06-93 18 ea d6 a9 8d ff 7b   R..;.&.........{
    0050 - a0 5e c8 c7 d0 8a 02 23-b7 b0 3f 0a 2f a5 21 93   .^.....#..?./.!.
    0060 - eb 9a c8 e0 3d d7 1f c5-31                        ....=...1

    Start Time: 1787651850
    Timeout   : 7200 (sec)
    Verify return code: 0 (ok)
    Extended master secret: no
    Max Early Data: 0
---
read R BLOCK
depth=3 C = US, O = Internet Security Research Group, CN = ISRG Root X1
verify return:1
depth=2 C = US, O = ISRG, CN = Root YR
verify return:1
depth=1 C = US, O = Let's Encrypt, CN = YR1
verify return:1
depth=0 CN = www.unde-pescuim.ro
verify return:1
DONE

```
`openssl s_client -connect undepescuim.vercel.app:443 -servername undepescuim.vercel.app -showcerts -verify_return_error` -> exit 0
```
CONNECTED(00000003)
---
Certificate chain
 0 s:CN = *.vercel.app
   i:C = US, O = Google Trust Services, CN = WR1
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Jun 28 13:27:57 2026 GMT; NotAfter: Sep 26 13:27:56 2026 GMT
-----BEGIN CERTIFICATE-----
MIIE+jCCA+KgAwIBAgIRALHCtgfflPKFE3ea4m/s+S8wDQYJKoZIhvcNAQELBQAw
OzELMAkGA1UEBhMCVVMxHjAcBgNVBAoTFUdvb2dsZSBUcnVzdCBTZXJ2aWNlczEM
MAoGA1UEAxMDV1IxMB4XDTI2MDYyODEzMjc1N1oXDTI2MDkyNjEzMjc1NlowFzEV
MBMGA1UEAwwMKi52ZXJjZWwuYXBwMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAj7MaGnUmCsjqcPfGepE4KaKcq4wXP5Sma9/61aXQ4f0W7jd0tE28HyTq
wU7wSOC4FoTv3/mSnxwc4gIe4+QxLHQSPspEMahRZNQYmYgFSaCwmRLDZsCKFH5J
HY7m7GbX9OWlUQc3h6yhSdbSMj98YlOvallFMXyzNDgXS4OaZ5oR+tzeeceEO63+
p2Foli5+Tsdep2mOctEOJ9BPdS5cg75wHnhkVXEACiFr85K9/qVsPF5NDTEw8wNf
ZVMnFQdon4tRFYMMCC2cH2KHUavSuS1OeyUTtYt0V68NDS/cq8QFfDnraB8Mj4eB
zVrB1xMLbX8c3iHEZT1+n347FvC3JwIDAQABo4ICGzCCAhcwDgYDVR0PAQH/BAQD
AgWgMBMGA1UdJQQMMAoGCCsGAQUFBwMBMAwGA1UdEwEB/wQCMAAwHQYDVR0OBBYE
FBuy8b80AsyumWmxRRF0+uBFWfNjMB8GA1UdIwQYMBaAFGZpSdTeKpyRA8+JDiS4
DjADboguMDUGCCsGAQUFBwEBBCkwJzAlBggrBgEFBQcwAoYZaHR0cDovL2kucGtp
Lmdvb2cvd3IxLmNydDAXBgNVHREEEDAOggwqLnZlcmNlbC5hcHAwEwYDVR0gBAww
CjAIBgZngQwBAgEwNgYDVR0fBC8wLTAroCmgJ4YlaHR0cDovL2MucGtpLmdvb2cv
d3IxL1UxZElTMnFqbHBRLmNybDCCAQMGCisGAQQB1nkCBAIEgfQEgfEA7wB2ANgJ
VTuUT3r/yBYZb5RPhauw+Pxeh1UmDxXRLnK7RUsUAAABnw6hRp8AAAQDAEcwRQIh
AOUeSrBb6H9mYaeEtYvzLvYcuJlGGdbqrUZr0RMfiirCAiAkGX5Z0Yryv//77ceO
0UXGMuERs9a6N0iuBNMCLBJA9AB1AMIxfldFGaNF7n843rKQQevHwiFaIr9/1bWt
dprZDlLNAAABnw6hRoIAAAQDAEYwRAIgTUgR1N7UYSEI4u0faZ//c/WnJpqGAP4p
GT0OccW+LicCIDqDbLoFsc+iuXP9yqaq0pykLnGenTxAesIy+NMjSPphMA0GCSqG
SIb3DQEBCwUAA4IBAQCwqGmMK85+NJPHoPxO5bqVVnT+P2/YCGWizqE+Lm+Pf+FS
sAFNqHH+xcYpHe7sIMI240MUvJZTz0XXG9srSRGCde5dLh95kfjerROLEbWnTux1
1lhi1Djjx1ck8A5CZ+EGEoCexiA3T0ONwOQB5kphqxi/ig2MuqC3c0SqFfZ5COFf
iCiEtH4HSlAMhfDsUtjPxQJzhwPp3Yj0M3wVz4WDRVGfXUDdYzNp6qqLW7s4eS8Z
0M1r2a0ZjwKQTZ5/ARgViCKMalKlO4u4KkLr6JBDKE4YsVUTFSf/J4QgSBJQtkPI
uXyV64ADs4w5CaleU/bQirhNe4sXRjbgwqsNUMVA
-----END CERTIFICATE-----
 1 s:C = US, O = Google Trust Services, CN = WR1
   i:C = US, O = Google Trust Services LLC, CN = GTS Root R1
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Dec 13 09:00:00 2023 GMT; NotAfter: Feb 20 14:00:00 2029 GMT
-----BEGIN CERTIFICATE-----
MIIFCzCCAvOgAwIBAgIQf9niwtIEigR0tieibQhopzANBgkqhkiG9w0BAQsFADBH
MQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExM
QzEUMBIGA1UEAxMLR1RTIFJvb3QgUjEwHhcNMjMxMjEzMDkwMDAwWhcNMjkwMjIw
MTQwMDAwWjA7MQswCQYDVQQGEwJVUzEeMBwGA1UEChMVR29vZ2xlIFRydXN0IFNl
cnZpY2VzMQwwCgYDVQQDEwNXUjEwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQDPbjYWircr7kaYAx1TcA937qNLoHK+jyMtwkfGj1yN+T3mGo7uMyINyRFI
uLBizvRpDXICfd7VJg/DbpvPfg7XIM/GkDujggbaOp3/bFa/3OlhlEXkabxPD8kT
wK1hRHIggdAPK55oamJqj4oiV3lpK+IkM352YyxdvFFpfiMHsf92gfHuuFi1azUV
76HmSCg5lzHZBx+Vp56uz5i8no2KA+Gwl01Qb5NMSh/4233xkJkVf+OW7e4xgepy
PVId3yVkpQtwqp7oqLlHyKdaECVgb0Lh1z/njwzwwoNGMyDmS3cEdqFop10VGO/Y
KHc1rQ6tRuRibuKq+MzvN34PJrMHAgMBAAGjgf4wgfswDgYDVR0PAQH/BAQDAgGG
MB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjASBgNVHRMBAf8ECDAGAQH/
AgEAMB0GA1UdDgQWBBRmaUnU3iqckQPPiQ4kuA4wA26ILjAfBgNVHSMEGDAWgBTk
rysmcRorSCeFL1JmLO/wiRNxPjA0BggrBgEFBQcBAQQoMCYwJAYIKwYBBQUHMAKG
GGh0dHA6Ly9pLnBraS5nb29nL3IxLmNydDArBgNVHR8EJDAiMCCgHqAchhpodHRw
Oi8vYy5wa2kuZ29vZy9yL3IxLmNybDATBgNVHSAEDDAKMAgGBmeBDAECATANBgkq
hkiG9w0BAQsFAAOCAgEATuazCBEgkWAn+VGQTQIY7rjBidUihJfm1t/mTjo7KQR+
3iDx4o2L06oeF0Q3wpKYpQgI/TeMqUlYMWQmZbWPE0PX8pfsVAE5E5tVOjh34bNA
JwDPVnsZVJwzN3nw5BGQ7sxRspFzIcM/qbbTpNeXf9II4Wsk2+Tv6FSVFZUL3/0u
HradbruDWjRQ4IZ7mYqKiEqk08dpOZ+TmBzwykEGy1/IXberb6Ap1SSnn2+RI7t6
N/fqPCrwwFjp8kg1G6etRATGBaPYCx+GjJMFPX+k97Alvoj3/98SvqdegLPYEPjv
xUclHpiKLD63NMmVarVQddIL6kOvTe5k0pnxRnR+mndGHIQc77TLbcZFeja56Pyn
lSqmer578c7CBrPqo1BVmPyWUK+v6sGuzs7Mq7QQaxVs4710cI/MpPp1ovxMVt17
ENKxLk34LpEKAKVmqwnzbHHRjhXNeCC984XDOwLEp0K4MzHl8ZOWJQAakCdVlFC+
PyA3GP2JX/QLoqWNHGuN9c9vLObDhHVs/L+65De+OdnnjpFGI9xxtsNyRsyaHdFA
f5z7ulOoXDXkHCCej/Ehs5docReNt16W2xbH/EBuirJrOzFE2rtALxksl1TdEjOf
IKXOJfUqQeVI5+hA7V+n1+A/n7Npg0S+5ODytWh5XW54ccN1drJnMK54ttozh0c=
-----END CERTIFICATE-----
 2 s:C = US, O = Google Trust Services LLC, CN = GTS Root R1
   i:C = BE, O = GlobalSign nv-sa, OU = Root CA, CN = GlobalSign Root CA
   a:PKEY: rsaEncryption, 4096 (bit); sigalg: RSA-SHA256
   v:NotBefore: Jun 19 00:00:42 2020 GMT; NotAfter: Jan 28 00:00:42 2028 GMT
-----BEGIN CERTIFICATE-----
MIIFYjCCBEqgAwIBAgIQd70NbNs2+RrqIQ/E8FjTDTANBgkqhkiG9w0BAQsFADBX
MQswCQYDVQQGEwJCRTEZMBcGA1UEChMQR2xvYmFsU2lnbiBudi1zYTEQMA4GA1UE
CxMHUm9vdCBDQTEbMBkGA1UEAxMSR2xvYmFsU2lnbiBSb290IENBMB4XDTIwMDYx
OTAwMDA0MloXDTI4MDEyODAwMDA0MlowRzELMAkGA1UEBhMCVVMxIjAgBgNVBAoT
GUdvb2dsZSBUcnVzdCBTZXJ2aWNlcyBMTEMxFDASBgNVBAMTC0dUUyBSb290IFIx
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAthECix7joXebO9y/lD63
ladAPKH9gvl9MgaCcfb2jH/76Nu8ai6Xl6OMS/kr9rH5zoQdsfnFl97vufKj6bwS
iV6nqlKr+CMny6SxnGPb15l+8Ape62im9MZaRw1NEDPjTrETo8gYbEvs/AmQ351k
KSUjB6G00j0uYODP0gmHu81I8E3CwnqIiru6z1kZ1q+PsAewnjHxgsHA3y6mbWwZ
DrXYfiYaRQM9sHmklCitD38m5agI/pboPGiUU+6DOogrFZYJsuB6jC511pzrp1Zk
j5ZPaK49l8KEj8C8QMALXL32h7M1bKwYUH+E4EzNktMg6TO8UpmvMrUpsyUqtEj5
cuHKZPfmghCN6J3Cioj6OGaK/GP5Afl4/Xtcd/p2h/rs37EOeZVXtL0m79YB0esW
CruOC7XFxYpVq9Os6pFLKcwZpDIlTirxZUTQAs6qzkm06p98g7BAe+dDq6dso499
iYH6TKX/1Y7DzkvgtdizjkXPdsDtQCv9Uw+wp9U7DbGKogPeMa3Md+pvez7W35Ei
Eua++tgy/BBjFFFy3l3WFpO9KWgz7zpm7AeKJt8T11dleCfeXkkUAKIAf5qoIbap
sZWwpbkNFhHax2xIPEDgfg1azVY80ZcFuctL7TlLnMQ/0lUTbiSw1nH69MG6zO0b
9f6BQdgAmD06yK56mDcYBZUCAwEAAaOCATgwggE0MA4GA1UdDwEB/wQEAwIBhjAP
BgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBTkrysmcRorSCeFL1JmLO/wiRNxPjAf
BgNVHSMEGDAWgBRge2YaRQ2XyolQL30EzTSo//z9SzBgBggrBgEFBQcBAQRUMFIw
JQYIKwYBBQUHMAGGGWh0dHA6Ly9vY3NwLnBraS5nb29nL2dzcjEwKQYIKwYBBQUH
MAKGHWh0dHA6Ly9wa2kuZ29vZy9nc3IxL2dzcjEuY3J0MDIGA1UdHwQrMCkwJ6Al
oCOGIWh0dHA6Ly9jcmwucGtpLmdvb2cvZ3NyMS9nc3IxLmNybDA7BgNVHSAENDAy
MAgGBmeBDAECATAIBgZngQwBAgIwDQYLKwYBBAHWeQIFAwIwDQYLKwYBBAHWeQIF
AwMwDQYJKoZIhvcNAQELBQADggEBADSkHrEoo9C0dhemMXoh6dFSPsjbdBZBiLg9
NR3t5P+T4Vxfq7vqfM/b5A3Ri1fyJm9bvhdGaJQ3b2t6yMAYN/olUazsaL+yyEn9
WprKASOshIArAoyZl+tJaox118fessmXn1hIVw41oeQa1v1vg4Fv74zPl6/AhSrw
9U5pCZEt4Wi4wStz6dTZ/CLANx8LZh1J7QJVj2fhMtfTJr9w4z30Z209fOU0iOMy
+qduBmpvvYuR7hZL6Dupszfnw0Skfths18dG9ZKb59UhvmaSGZRVbNQpsg3BZlvi
d0lIKO2d1xozclOzgjXPYovJJIultzkMu34qQb9Sz/yilrbCgj8=
-----END CERTIFICATE-----
---
Server certificate
subject=CN = *.vercel.app
issuer=C = US, O = Google Trust Services, CN = WR1
---
No client certificate CA names sent
Peer signing digest: SHA256
Peer signature type: RSA-PSS
Server Temp Key: X25519, 253 bits
---
SSL handshake has read 4509 bytes and written 388 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_128_GCM_SHA256
Server public key is 2048 bit
Secure Renegotiation IS NOT supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
Early data was not sent
Verify return code: 0 (ok)
---
---
Post-Handshake New Session Ticket arrived:
SSL-Session:
    Protocol  : TLSv1.3
    Cipher    : TLS_AES_128_GCM_SHA256
    Session-ID: F6FC31151CAB0B344027003527875EF70256D8301801061B6E4D7AE6BE92B0BB
    Session-ID-ctx: 
    Resumption PSK: C5441D0B88198716463D17B29DEA13EB95F797DBB7C482531855927306C83FFC
    PSK identity: None
    PSK identity hint: None
    SRP username: None
    TLS session ticket lifetime hint: 604800 (seconds)
    TLS session ticket:
    0000 - e7 01 e2 4c e4 46 60 28-77 9e d1 36 84 3e 45 9d   ...L.F`(w..6.>E.
    0010 - c5 f9 66 cf da 15 96 02-b4 d1 98 2b 09 36 94 80   ..f........+.6..
    0020 - 1a c3 45 8f 79 0d 4e df-49 ef 06 86 c4 79 2e 41   ..E.y.N.I....y.A
    0030 - 57 3b 35 01 80 bc 46 34-d5 dd 28 e3 47 66 a4 8f   W;5...F4..(.Gf..
    0040 - 7e 86 bf d8 3c 0c 14 d4-c4 c5 de 5a 58 25 12 b9   ~...<......ZX%..
    0050 - 6a 28 11 d7 60 70 8d 66-d0 ee 5b 79 98 4c 04 5b   j(..`p.f..[y.L.[
    0060 - 3b a6 3e fc c9 08 b6 e0-14                        ;.>......

    Start Time: 1787651850
    Timeout   : 7200 (sec)
    Verify return code: 0 (ok)
    Extended master secret: no
    Max Early Data: 0
---
read R BLOCK
depth=2 C = US, O = Google Trust Services LLC, CN = GTS Root R1
verify return:1
depth=1 C = US, O = Google Trust Services, CN = WR1
verify return:1
depth=0 CN = *.vercel.app
verify return:1
DONE

```
### DNS email records
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=MX` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":15}],"Answer":[{"name":"unde-pescuim.ro","type":15,"TTL":286,"data":"12 route2.mx.cloudflare.net."},{"name":"unde-pescuim.ro","type":15,"TTL":286,"data":"36 route3.mx.cloudflare.net."},{"name":"unde-pescuim.ro","type":15,"TTL":286,"data":"66 route1.mx.cloudflare.net."}]}
```
`GET https://cloudflare-dns.com/dns-query?name=_dmarc.unde-pescuim.ro&type=TXT` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"_dmarc.unde-pescuim.ro","type":16}],"Answer":[{"name":"_dmarc.unde-pescuim.ro","type":16,"TTL":300,"data":"\"v=DMARC1; p=none; rua=mailto:contact@unde-pescuim.ro; adkim=s; aspf=s; pct=100\""}]}
```
`GET https://cloudflare-dns.com/dns-query?name=unde-pescuim.ro&type=TXT` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro","type":16}],"Answer":[{"name":"unde-pescuim.ro","type":16,"TTL":300,"data":"\"v=spf1 include:_spf.mx.cloudflare.net ~all\""}]}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=MX` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":15}],"Answer":[{"name":"unde-pescuim.ro.","type":15,"TTL":300,"data":"36 route3.mx.cloudflare.net."},{"name":"unde-pescuim.ro.","type":15,"TTL":300,"data":"12 route2.mx.cloudflare.net."},{"name":"unde-pescuim.ro.","type":15,"TTL":300,"data":"66 route1.mx.cloudflare.net."}],"Comment":"Response from 108.162.193.73."}
```
`GET https://dns.google/resolve?name=_dmarc.unde-pescuim.ro&type=TXT` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"_dmarc.unde-pescuim.ro.","type":16}],"Answer":[{"name":"_dmarc.unde-pescuim.ro.","type":16,"TTL":300,"data":"v=DMARC1; p=none; rua=mailto:contact@unde-pescuim.ro; adkim=s; aspf=s; pct=100"}],"Comment":"Response from 172.64.34.2."}
```
`GET https://dns.google/resolve?name=unde-pescuim.ro&type=TXT` -> HTTP 200
```json
{"Status":0,"TC":false,"RD":true,"RA":true,"AD":true,"CD":false,"Question":[{"name":"unde-pescuim.ro.","type":16}],"Answer":[{"name":"unde-pescuim.ro.","type":16,"TTL":300,"data":"v=spf1 include:_spf.mx.cloudflare.net ~all"}],"Comment":"Response from 108.162.193.73."}
```

## Parsed HTML, certificate and endpoint checks

Command: `python3` probe using `urllib.request.urlopen()` against `https://unde-pescuim.ro`, `https://www.unde-pescuim.ro`, and `https://undepescuim.vercel.app`; body regexes for canonical, Open Graph, JSON-LD and `vercel.app` references.

Exact output (run 2):
```
URL https://unde-pescuim.ro status 200 bytes 25708
canonical= []
og= []
jsonld= 0
vercel_refs= []

URL https://www.unde-pescuim.ro status 200 bytes 25708
canonical= []
og= []
jsonld= 0
vercel_refs= []

URL https://undepescuim.vercel.app status 200 bytes 25708
canonical= []
og= []
jsonld= 0
vercel_refs= []
```

Command: `openssl s_client -connect HOST:443 -servername HOST </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName`

Exact output:
```
CERT unde-pescuim.ro
subject=CN = unde-pescuim.ro
issuer=C = US, O = Let's Encrypt, CN = YR2
notBefore=Aug 24 09:31:48 2026 GMT
notAfter=Nov 22 09:31:47 2026 GMT
X509v3 Subject Alternative Name:
    DNS:unde-pescuim.ro

CERT www.unde-pescuim.ro
subject=CN = www.unde-pescuim.ro
issuer=C = US, O = Let's Encrypt, CN = YR1
notBefore=Aug 24 09:31:49 2026 GMT
notAfter=Nov 22 09:31:48 2026 GMT
X509v3 Subject Alternative Name:
    DNS:www.unde-pescuim.ro

CERT undepescuim.vercel.app
subject=CN = *.vercel.app
issuer=C = US, O = Google Trust Services, CN = WR1
notBefore=Jun 28 13:27:57 2026 GMT
notAfter=Sep 26 13:27:56 2026 GMT
X509v3 Subject Alternative Name:
    DNS:*.vercel.app
```

Interpretation: apex and www both return HTTPS 200; neither redirects. HTTP apex and HTTP www each return 308 to their own HTTPS URL. The required static routes `/robots.txt` and `/sitemap.xml` return 404; `/manifest.webmanifest` returns 200; `/data/waters.json` returns 200 with `Content-Length: 10599467`. Required canonical, Open Graph and JSON-LD metadata are absent from all three HTML bodies. No stale `vercel.app` URL reference was found in those bodies. CSP, HSTS and other security headers are present in the exact header captures above.

## Findings and next actions

- DNSSEC: at least one DoH response reports AD=true.
- At least one HTTPS/HTTP probe returned a 2xx response.
- No explicit OpenSSL certificate verification error appeared in captured output.
- Fallback vercel.app host was probed; inspect status and headers above.
- Parsed checks above are the release/configuration follow-up: `/robots.txt` and `/sitemap.xml` are 404; canonical/Open Graph/JSON-LD tags are absent; CSP and HSTS are present; no stale `vercel.app` URL reference appears in the HTML.
- Email forwarding test prerequisite: confirm DMARC policy and Email Routing MX/TXT records above, then perform a separate human-controlled forwarding test with a non-sensitive message.

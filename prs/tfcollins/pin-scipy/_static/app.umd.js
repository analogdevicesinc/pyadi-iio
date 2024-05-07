!function(e,t){"object"==typeof exports&&"undefined"!=typeof module?module.exports=t():"function"==typeof define&&define.amd?define(t):(e="undefined"!=typeof globalThis?globalThis:e||self).App=t()}(this,(function(){"use strict";class e{constructor(e,t){if(this.$,"string"!=typeof e)return void(this.$=e);let s=["innerText","className","id","title","innerText","value","tabIndex","role","href","ariaPressed","preload","controls","autoplay","src","placeholder","htmlFor","type","autocomplete","name","accept","disabled","innerHTML","action"];if(this.$=document.createElement(e),"object"==typeof t)for(const e in t)s.includes(e)?this.$[e]=t[e]:this.$.dataset[e]=t[e]}set innerText(e){this.$.innerText=e}get innerText(){return this.$.innerText}get height(){return this.$.offsetHeight}get width(){return this.$.offsetWidth}get id(){return this.$.id}set id(e){this.$.id=e}get value(){return this.$.value}set value(e){this.$.value=e}get src(){return this.$.src}set src(e){this.$.src=e}focus(){this.$.focus()}get classList(){return this.$.classList}get style(){return this.$.style}onchange(e,t,s){return this.$.onchange=r=>{void 0===s?t.apply(e,[r]):s.constructor==Array&&(s.push(r),t.apply(e,s))},this}onclick(e,t,s){return this.$.onclick=r=>{void 0===s?t.apply(e,[r]):s.constructor==Array&&(s.push(r),t.apply(e,s))},this}onup(e,t,s){return this.$.addEventListener("mouseup",(r=>{void 0===s?t.apply(e,[r]):s.constructor==Array&&(s.push(r),t.apply(e,s))})),this}ondown(e,t,s){return this.$.addEventListener("mousedown",(r=>{void 0===s?t.apply(e,[r]):s.constructor==Array&&(s.push(r),t.apply(e,s))})),this}onmove(e,t,s){return this.$.addEventListener("mousemove",(r=>{void 0===s?t.apply(e,[r]):s.constructor==Array&&(s.push(r),t.apply(e,s))})),this}onevent(e,t,s,r){return this.$.addEventListener(e,(e=>{void 0===r?s.apply(t,[e]):r.constructor==Array&&(r.push(e),s.apply(t,r))})),this}append(e){return e.constructor!=Array&&(e=[e]),e.forEach((e=>{/HTML(.*)Element/.test(e.constructor.name)?this.$.appendChild(e):"object"==typeof e&&/HTML(.*)Element/.test(e.$)&&this.$.appendChild(e.$)})),this}delete(){this.$.remove()}removeChilds(){let e=this.$.lastElementChild;for(;e;)this.$.removeChild(e),e=this.$.lastElementChild;return this}static get(t,s){return void 0===(s=s instanceof e?s.$:s)?document.querySelector(t):s.querySelector(t)}static getAll(t,s){return"object"==typeof(s=s instanceof e?s.$:s)?s.querySelectorAll(t):get(s).querySelectorAll(t)}static switchState(t,s){let r=null!=s?s:"on";(t=t instanceof e?t.$:t).classList.contains(r)?t.classList.remove(r):t.classList.add(r)}static UID(){return(+new Date).toString(36)+Math.random().toString(36).substr(2)}static prototypeDetails(t){let s=new e("summary",{innerText:t.innerText}),r=new e("details",{id:t.id,name:t.id}).append(s);return null!=t.onevent&&t.onevent.forEach((e=>{e.args.push(r.$),s.onevent(e.event,e.self,e.fun,e.args)})),r}static prototypeInputFile(t){return new e("label",{htmlFor:`${t.id}_input`,id:t.id,className:t.className,innerText:t.innerText}).append(new e("input",{id:`${t.id}_input`,type:"file"}))}static prototypeCheckSwitch(t){let s=new e("input",{id:t.id,name:t.id,className:"checkswitch",type:"checkbox",value:!1});return[s,new e("div",{className:t.className}).append([new e("div").append([new e("label",{className:"checkswitch",htmlFor:t.id,innerText:t.innerText}).append([s,new e("span")])])])]}static prototypeDownload(e,t){let s,r=/.*\.(py|xml|csv|json|svg|png)$/;if(!r.test(e))return;let n=e.match(r)[1];switch(e=e.replaceAll("/","-").replaceAll(" ","_").toLowerCase(),n){case"xml":s="data:x-application/xml;charset=utf-8,"+encodeURIComponent(t);break;case"py":s="data:text/python;charset=utf-8,"+encodeURIComponent(t);break;case"json":s="data:text/json;charset=utf-8,"+encodeURIComponent(t);break;case"csv":s="data:text/csv;charset=utf-8,"+encodeURIComponent(t);break;case"svg":s="data:image/svg+xml;charset=utf-8,"+encodeURIComponent(t);break;case"png":s=t}let a=document.createElement("a");a.setAttribute("href",s),a.setAttribute("download",e),a.style.display="none",document.body.appendChild(a),a.click(),document.body.removeChild(a)}static setSelected(e,t){for(var s=0;s<e.$.options.length;s++)if(e.$.options[s].text==t)return void(e.$.options[s].selected=!0)}static lazyUpdate(t,s,r,n){n=null==n?"innerText":n;let a=e.get(`[data-uid='${s}']`,t);for(const t in r)e.get(`#${t}`,a)[n]=r[t]}}let t=new class{constructor(){this.portrait=!1,this.isLocal="file:"==window.location.protocol,this.currentTheme=localStorage.getItem("theme");let t=this.$={};t.body=new e(e.get("body")),null===this.currentTheme&&(this.currentTheme=this.getOSTheme()),t.body.classList.add("js-on"),this.currentTheme!==this.getOSTheme()&&t.body.classList.add(this.currentTheme),t.searchButton=new e("button",{id:"search",title:"Search"}).onclick(this,(()=>{e.switchState(t.searchArea),e.switchState(t.searchAreaBg),t.searchBox.focus(),t.searchBox.$.select()})),t.changeTheme=new e("button",{className:"dark"===this.currentTheme?"icon on":"icon",id:"theme",title:"Switch theme"}).onclick(this,(()=>{t.body.classList.remove(this.currentTheme),this.currentTheme="dark"===this.currentTheme?"light":"dark",this.getOSTheme()==this.currentTheme?localStorage.removeItem("theme"):(localStorage.setItem("theme",this.currentTheme),t.body.classList.add(this.currentTheme))})),t.searchAreaBg=new e("div",{className:"search-area-bg"}).onclick(this,(()=>{e.switchState(t.searchArea),e.switchState(t.searchAreaBg)})),t.searchArea=new e(e.get("form.search-area")),t.searchBox=new e(e.get("form.search-area input")),t.searchArea.$.action=e.get('link[rel="search"]').href,t.body.append([t.searchAreaBg]),t.rightHeader=new e(e.get(".header #right span.reverse")).append([t.changeTheme,t.searchButton])}search(t){"IntlRo"!==t.code||this.$.searchArea.classList.contains("on")?"Escape"===t.code&&this.$.searchArea.classList.contains("on")&&(e.switchState(this.$.searchArea),e.switchState(this.$.searchAreaBg)):(e.switchState(this.$.searchArea),e.switchState(this.$.searchAreaBg),this.$.searchBox.focus(),this.$.searchBox.$.select())}init(){onresize=()=>{t.portrait=window.innerHeight>window.innerWidth},document.addEventListener("keyup",(e=>{this.search(e)}),!1)}setState(e,t){e.forEach((e=>{t?e.classList.add("on"):e.classList.remove("on")}))}getOSTheme(){return window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}};function s(){window.app={},app.navigation=t,app.navigation.init()}return s(),s}));
//# sourceMappingURL=app.umd.js.map
"""Flippable flashcard deck (self-contained HTML so the flip animation works)."""
import json

import streamlit.components.v1 as components

_HTML = """
<style>
 body{margin:0;font-family:'IBM Plex Sans',sans-serif;color:#1B2430}
 .wrap{max-width:460px;margin:0 auto;text-align:center}
 .card{perspective:1000px;height:230px;cursor:pointer}
 .in{position:relative;width:100%;height:100%;transform-style:preserve-3d;transition:transform .5s}
 .card.flip .in{transform:rotateY(180deg)}
 .face{position:absolute;inset:0;backface-visibility:hidden;border:1px solid #c9ccc2;border-radius:6px;
  background:#FBFBF8;display:flex;align-items:center;justify-content:center;padding:1.4rem;
  font-family:'Fraunces',Georgia,serif;font-size:1.2rem;line-height:1.35;box-sizing:border-box}
 .back{transform:rotateY(180deg);background:#DCE4DC}
 .bar{display:flex;align-items:center;justify-content:space-between;margin-top:.9rem;font-size:.85rem}
 button{border:1px solid #c9ccc2;background:#FBFBF8;border-radius:3px;padding:.4rem .9rem;cursor:pointer}
 button:disabled{opacity:.4;cursor:default}
</style>
<div class="wrap">
 <div class="card" id="c" tabindex="0"><div class="in"><div class="face" id="f"></div><div class="face back" id="b"></div></div></div>
 <div class="bar"><button id="p">Previous</button><span id="n"></span><button id="x">Next</button></div>
 <div style="font-size:.78rem;opacity:.6;margin-top:.5rem">Click the card to flip it</div>
</div>
<script>
 const cards=__CARDS__; let i=0;
 const c=document.getElementById('c');
 function show(){c.classList.remove('flip');
  document.getElementById('f').textContent=cards[i].front;
  document.getElementById('b').textContent=cards[i].back;
  document.getElementById('n').textContent=(i+1)+' / '+cards.length;
  document.getElementById('p').disabled=i===0;document.getElementById('x').disabled=i===cards.length-1}
 c.onclick=()=>c.classList.toggle('flip');
 c.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();c.classList.toggle('flip')}};
 document.getElementById('p').onclick=()=>{i--;show()};
 document.getElementById('x').onclick=()=>{i++;show()};
 show();
</script>
"""


def render(cards, height=330):
    payload = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    components.html(_HTML.replace("__CARDS__", payload), height=height)

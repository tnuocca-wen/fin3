console.log("Hi");


function clearSearch() {
  document.getElementById('company_field').value = '';
}


companies = null;

prev_doc = "";

let lastScrollY = 0;

window.addEventListener("scroll", function (e) {
  e.preventDefault();
  console.log("jijji");
  const floatingDiv = document.querySelector(".floating-nav");
  const displayDiv = document.querySelector("#display_div");
  const currentScrollY = window.scrollY;

  if (currentScrollY > lastScrollY) {
    // Scrolling down
    // floatingDiv.classList.add("d-none");
    // senti.classList.add("d-none");
    senti.style.visibility = "hidden";
    displayDiv.scrollIntoView({ behavior: "smooth", block: "start" });
    // window.scroll(1,0);
    // displayDiv.classList.add("fixed-top");
    // lastScrollY = currentScrollY;
  } else {
    // Scrolling up
    senti.style.visibility = "visible";
    // senti.classList.remove("d-none");
    // floatingDiv.classList.remove("d-none");
    // displayDiv.classList.remove("fixed-top");
  }
  // lastScrollY = currentScrollY;
});

function growLoader() {
  pdfToggleDiv.innerHTML = ``;
  if (fin_parent.innerHTML != ''){
    fin_parent.innerHTML = '';
  }
  document.getElementById(
    "status"
  ).innerHTML = `<div class="spinner-grow" style="border-radius: .5px;" role="status" style="margin-top: 2%;">
                                                      <span class="visually-hidden">Loading...</span>
                                                        </div>`;
  if (document.getElementById("fin_text")) {
    document.getElementById("fin_text").remove();}
  if (document.getElementById("pdf_parent").innerHTML != ``) {
    pdf_parent.classList.remove("col", "mx-auto");
    pdf_parent.innerHTML = ``;
  }
}

// function circLoader() {
//   pdfToggleDiv.innerHTML = ``;
//   if (fin_parent.innerHTML != ''){
//     fin_parent.innerHTML = '';
//   }
//   document.getElementById(
//     "status"
//   ).innerHTML = `<div class="" style="border-radius: .5px;" role="" style="margin-top: 2%;">
//                                                       <span class="loader2">Loading...</span>
//                                                         </div>`;
//   if (document.getElementById("fin_text")) {
//     document.getElementById("fin_text").remove();
//     if (document.getElementById("pdf_doc")) {
//       document.getElementById("pdf_doc").remove();
//     }
//   }
// }



// function sentiment_ret(cselect) {
//   senti_content.innerHTML = ``;
//   prev = [cselect, yselect.value, qselect.value];
//   sentiform = new FormData();
//   selected_s = [cselect, yselect.value, qselect.value];
//   sentiform.append("selected", JSON.stringify(selected_s));
//   // sentiform.append("ticker", cselect);
//   var out = 0;
//   fetch(senti_url, {
//     method: "POST",
//     body: sentiform,
//     headers: {
//       "X-CSRFToken": csrf_token,
//     },
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       out = 1;
//       if (data.status == 404) {
//         console.log(data.errors);
//         senti_content.innerHTML = `<div class="mx-auto p-2" style="display: block; font-size: small;">Setiment data unavilable</div>`;
//       } else {
//         score = data.score;
//         sarray = score.split("\n");
//         for (i = 0; i < sarray.length; i++) {
//           sarray[i] = Math.round((sarray[i] * 10000) / 100);
//         }
//         pos = data.pos;
//         neg = data.neg;
//         neu = data.neu;
//         senti_content.innerHTML = `<button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasScrolling" aria-controls="offcanvasScrolling">Sentiment</button>`;
//         // `<div class="p-2" style="display: block;">Positive: <a class="hyperlink" id="poss" data-bs-toggle="modal" data-bs-target="#sentimentmodal">${sarray[0]}%</a>, Negative: <a class='hyperlink' id="negs" data-bs-toggle="modal" data-bs-target="#sentimentmodal">${sarray[2]}%</a> and Neutral: <a class='hyperlink' id="neus" data-bs-toggle="modal" data-bs-target="#sentimentmodal">${sarray[1]}%</a>`;
//         // poss.addEventListener("click", () => {
//         //   sentimentmodalLabel.innerText = "Sentiment - Positive";
//         //   sentiment_sentences.innerText = pos;
//         // });
//         // negs.addEventListener("click", () => {
//         //   sentimentmodalLabel.innerText = "Sentiment - Negative";
//         //   sentiment_sentences.innerText = neg;
//         // });
//         // neus.addEventListener("click", () => {
//         //   sentimentmodalLabel.innerText = "Sentiment - Neutral";
//         //   sentiment_sentences.innerText = neu;
//         // });
        
//       }
//     })
//     .catch((error) => {
//       console.error(error);
//     });
//     return out;
// }

var sent_dat = [];
function sentiment_ret(cselect) {
  sent_dat = [];
  senti_content.innerHTML = ``;
  prev = [cselect, yselect.value, qselect.value];
  sentiform = new FormData();
  sentiform.append("ticker", cselect);
  fetch(senti_url, {
    method: "POST",
    body: sentiform,
    headers: {
      "X-CSRFToken": csrf_token,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status == 404) {
        console.log(data.errors);
        senti_content.innerHTML = `<div class="mx-auto p-2" style="display: block; font-size: small;">Setiment data unavilable</div>`;
      } else {
        var scores = data.scores;
        var posd = data.pos;
        var negd = data.neg;
        var neud = data.neu;       
        let tosort = [];
        scores.forEach(el => {
          let tstrn = parseInt(el[0]+el[1]);
          tosort.push(tstrn);
        });
        for (let i=0; i<tosort.length-1; i++){
          for (let j=0;j<tosort.length-i-1;j++){
          if (tosort[j] < tosort[j+1]){
            [tosort[j], tosort[j + 1]] = [tosort[j + 1], tosort[j]];
            [scores[j], scores[j + 1]] = [scores[j + 1], scores[j]];
            [posd[j], posd[j + 1]] = [posd[j + 1], posd[j]];
            [negd[j], negd[j + 1]] = [negd[j + 1], negd[j]];
            [neud[j], neud[j + 1]] = [neud[j + 1], neud[j]];
          }
        }}
        sent_dat.push(posd, negd, neud);
        sentibdy = document.querySelector(".offcanvas-body");
        sentibdy.innerHTML = ``;
        var table = document.createElement("table");
        table.classList.add('table',  'table-hover');
        var thead = document.createElement('thead');
        var headerRow = document.createElement('tr');
        cols = ["Year", "Quarter", "Sentiment"];
        for (i=0; i<cols.length; i++){
          var th = document.createElement("th");
          th.textContent = cols[i];
          headerRow.appendChild(th);
        }
        thead.appendChild(headerRow);
        table.appendChild(thead);

        var tbody = document.createElement('tbody');
        scores.forEach(score => {
          var row = document.createElement('tr');
          for (i = 0; i<score.length; i++) {
            if(i==2){
              var dat = document.createElement('td');
              td_contain = document.createElement("div");
              td_contain.classList.add("td_contain");
              for (j=0; j<score[i].length; j++){
                innerdiv = document.createElement("div");
                innerdiv.classList.add("unit");
                if (j==0){innerdiv.classList.add("pos");
                innerdiv.innerHTML = `<a class="hyperlink" id="poss" data-bs-toggle="modal" data-bs-target="#sentimentmodal" onclick="sent_disp(`+score[0]+`,`+score[1]+`,`+`1)">`+Math.round((score[i][j]*10000)/100)+`%</a>`;}
                if (j==1){innerdiv.classList.add("neu");
                innerdiv.innerHTML = `<a class="hyperlink" id="neus" data-bs-toggle="modal" data-bs-target="#sentimentmodal" onclick="sent_disp(`+score[0]+`,`+score[1]+`,`+`2)">`+Math.round((score[i][j]*10000)/100)+`%</a>`;}
                if (j==2){innerdiv.classList.add("neg");
                innerdiv.innerHTML = `<a class="hyperlink" id="negs" data-bs-toggle="modal" data-bs-target="#sentimentmodal" onclick="sent_disp(`+score[0]+`,`+score[1]+`,`+`3)">`+Math.round((score[i][j]*10000)/100)+`%</a>`;}
                // innerdiv.innerHTML = `<a class="hyperlink">`+Math.round((score[i][j]*10000)/100)+`</a>`;
                td_contain.appendChild(innerdiv);
              }
              dat.appendChild(td_contain);
              row.appendChild(dat);
            }
            else{
            var dat = document.createElement('td');
            dat.textContent = score[i];
            row.appendChild(dat);
          }
          }
          tbody.appendChild(row);
        });
        table.appendChild(tbody);

        sentibdy.appendChild(table);
      }
      senti_content.innerHTML = `<button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasScrolling" aria-controls="offcanvasScrolling">Sentiment</button>`;
      // poss.addEventListener("click", () => {
      //   sentimentmodalLabel.innerText = "Sentiment - Positive";
      //   sentiment_sentences.innerText = pos;
      // });
      // negs.addEventListener("click", () => {
      //   sentimentmodalLabel.innerText = "Sentiment - Negative";
      //   sentiment_sentences.innerText = neg;
      // });
      // neus.addEventListener("click", () => {
      //   sentimentmodalLabel.innerText = "Sentiment - Neutral";
      //   sentiment_sentences.innerText = neu;
      // });
    })
    .catch((error) => {

    });
  }

function sent_disp(year, qrtr, senti) {
  if (senti == 1){
    sent_dat[0].forEach(item => {
      if (item[0] == year && item[1] == qrtr){
        sentimentmodalLabel.innerText = "Sentiment - Positive";
        sentiment_sentences.innerText = item[2];
      }
    });
  }
  else if (senti == 2){
    sent_dat[2].forEach(item => {
      if (item[0] == year && item[1] == qrtr){
        sentimentmodalLabel.innerText = "Sentiment - Neutral";
        sentiment_sentences.innerText = item[2];
      }
    });
  }
  else if (senti == 3){
    sent_dat[1].forEach(item => {
      if (item[0] == year && item[1] == qrtr){
        sentimentmodalLabel.innerText = "Sentiment - Negative";
        sentiment_sentences.innerText = item[2];
      }
    });
  }
}

var ktdata = [];
function data_ret(cselect) {
  formdata = new FormData();
  selected = [cselect, yselect.value, qselect.value, sselect.value];
  formdata.append("selected", JSON.stringify(selected));
  fetch(selection_form.action, {
    method: "POST",
    body: formdata,
    headers: {
      "X-CSRFToken": csrf_token,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.errors) {
        // Handle form validation errors
        console.log(data.errors);
      } else {
        console.log(data.status);
        if (data.status == 200) {
          if (!document.getElementById("fin_text")) {
            if (document.getElementById("status")) {
              document.getElementById("status").innerText = "";
            }
            pdf_src =
              doc_root +
              data.ticker +
              "/" +
              data.year +
              "/" +
              data.qrtr +
              "/" +
              data.ticker +
              ".pdf";
            pdfbtn_create(pdf_src);
            const fin_text = document.createElement("div");
            fin_text.id = "fin_text";
            fin_text.style.overflowY = "auto";
            fin_text.style.height = "97vh";
            fin_text.style.border = "1px dashed gray;";
            if (data.ktr == 1) {
              // console.log(data.ktdata);
              ktdata = data.ktdata;
              ktaways = data.text.split("\n");
              kthtml = ``;
              for (i = 0; i < ktaways.length; i++) {
                if (i == 0) {
                  kthtml += `<p>` + ktaways[i] + `</p>`;
                } else {
                  if (ktaways[i].trim() === ''){
                    ktaways.splice(i, 1);
                    i--;
                    // kthtml +=
                    //   `<p class="ktaways" onclick="elaborate(this)" data-bs-toggle="modal" data-bs-target="#sentimentmodal" id="ktaways` +
                    //   i-1 +
                    //   `">` +
                    //   ktaways[i] +
                    //   `</p>`;
                    // continue;
                  }
                  else{
                    kthtml +=
                      `<p class="ktaways" onclick="elaborate(this)" data-bs-toggle="modal" data-bs-target="#sentimentmodal" id="ktaways` +
                      i +
                      `">` +
                      ktaways[i] +
                      `</p>`;
                  }
                }
              }
              fin_text.innerHTML = kthtml;
            } else {
              fin_text.innerText = data.text;
            }
            document.getElementById("fin_parent").appendChild(fin_text);
          } else {
            pdf_src =
              doc_root +
              data.ticker +
              "/" +
              data.year +
              "/" +
              data.qrtr +
              "/" +
              data.ticker +
              ".pdf";
            fin_text.innerText = data.text;
          }
        } else {
          document.getElementById("status").innerHTML = ``;
          stats = document.getElementById("status");
          stats.style.textAlign = "center";
          console.log(data.pdf);
          if (data.status == 404) {
            stats.innerHTML = `<a>No such company available.</a>`;
          } else {
            go = 0;
            if (data.pdf) {
              // console.log(data.pdf);
              // for(i=0;i<data.pdfs.length;i++){
              //   if (data.pdfs[i] != '')
              //   { go = i; }
              //   else{
              //     go = 0;
              //   }
              // }
              // if (go != 0)
              // {
              fin_parent.innerHTML =
                `<a class="btn btn-primary genbtn" target="_blank" id="gen_btn" href=` + data.pdf + `>Generate</a>`;
              generate(data.ticker, data.year, data.qrtr, sselect.value);
              // }
            } else {
              stats.innerHTML = `<a>PDFs are not available</a>`;
            }
          }
        }
      }
    })
    .catch((error) => {
      // Handle any network or server errors
      // console.log("this is the form data:", formdata)
      console.error(error);
    });
}

function elaborate(elem) {
  id = parseInt(elem.id.slice(7));
  sentimentmodalLabel.innerText = "Elaborated";
  if (ktdata[0][id - 1] != ''){
    q1 = ktdata[0][id - 1];}
  else{
    q1 = `<button id="q1gen" onclick="strtktelab(1,`+id+`)" class="btn btn-primary">Generate</button>`;
  }
  if (ktdata[1][id - 1] != ''){
    q2 = ktdata[1][id - 1];}
  else{
    q2 = `<button id="q2gen" onclick="strtktelab(2,`+id+`)" class="btn btn-primary">Generate</button>`;
  }
  console.log(ktdata[2]);
  if (ktdata[2][id - 1] != ''){
    q3 = ktdata[2][id - 1];}
  else{
    q3 = `<button id="q3gen" onclick="strtktelab(3,`+id+`)" class="btn btn-primary">Generate</button>`;
    }
  sentiment_sentences.innerHTML = `<div><h3>Current Quarter</h3>`+`<div>`+q1+`</div></div>`+`<br>`+
  `<div><h3>Last Quarter</h3>`+`<div>`+q2+`</div></div>`+`<br>`+
  `<div><h3>The Quarter before the above..</h3>`+`<div>`+q3+`</div></div>`;
  
}

function sktdat(){
  console.log("Inside ktdat");
  formdata = new FormData();
  selected = [cur[0], cur[1], cur[2], 2];
  formdata.append("selected", JSON.stringify(selected));
  fetch(selection_form.action, {
    method: "POST",
    body: formdata,
    headers: {
      "X-CSRFToken": csrf_token,
    },
  }).then((response) => response.json())
  .then((data) => {
    if (data.ktr == 1) {
      // console.log(data.ktdata);
      ktdata = data.ktdata;
      ktaways = data.text.split("\n");
      kthtml = ``;
      for (i = 0; i < ktaways.length; i++) {
        if (i == 0) {
          kthtml += `<p>` + ktaways[i] + `</p>`;
        } else {
          if (ktaways[i].trim() === ''){
            ktaways.splice(i, 1);
            i--;
            // kthtml +=
            //   `<p class="ktaways" onclick="elaborate(this)" data-bs-toggle="modal" data-bs-target="#sentimentmodal" id="ktaways` +
            //   i-1 +
            //   `">` +
            //   ktaways[i] +
            //   `</p>`;
            // continue;
          }
          else{
            kthtml +=
              `<p class="ktaways" onclick="elaborate(this)" data-bs-toggle="modal" data-bs-target="#sentimentmodal" id="ktaways` +
              i +
              `">` +
              ktaways[i] +
              `</p>`;
          }
        }
      }
      fin_text.innerHTML = kthtml;
    } else {
      fin_text.innerText = data.text;
    }
    document.getElementById("fin_parent").appendChild(fin_text);
  });
  // ktid = "ktaways"+id-1;
  // ktid.click();
}


var selection_form = document.getElementById("selection-form");
var qselect = document.getElementById("QuarterSelect");
var sselect = document.getElementById("ServiceSelect");
var yselect = document.getElementById("YearSelect");
var coselect = document.getElementById("company_field");

ktdata = null;

// document.addEventListener("keydown", (e) => {
//   if (e.keyCode == 13) {
//     if (coselect.value != "") {
//       document.getElementById("submit-btn").click();
//     }
//   }
// });

qselect.addEventListener("change", (e) => {
  growLoader();
  // setTimeout(() => {
    document.getElementById("submit-btn").click();
  // }, 2000);
});

yselect.addEventListener("change", (e) => {
  growLoader();
  // setTimeout(() => {
    document.getElementById("submit-btn").click();
  // }, 2000);
});

sselect.addEventListener("change", (e) => {
  growLoader();
  // setTimeout(() => {
    document.getElementById("submit-btn").click();
  // }, 2000);
});

cur = [];
prev = [];

document.getElementById("submit-btn").addEventListener("click", function (e) {
  e.preventDefault();
  for (i = 0; i < companies.length; i++) {
    if (coselect.value === companies[i][0]) {
      var cselect = companies[i][1];
      console.log(cselect);
      break;
    }
  }
  cur = [cselect, yselect.value, qselect.value];
  // for (i = 0; i < 3; i++) {
  if (prev[0] == cur[0]) {
    eq = true;
  } else {
    eq = false;
    // break;
  }
  // }
  growLoader();
  if (!eq) {
    sentiment_ret(cselect);
  }
  data_ret(cselect);
});


function pdfbtn_create(src) {
  const pdf_btn = document.createElement("input");
  pdf_parent.classList.remove("col", "mx-auto");
  pdf_btn.type = "checkbox";
  pdf_btn.id = "pdf_toggle";
  pdf_btn.classList.add("btn-check");
  pdfbtn_label = document.createElement("label");
  pdfbtn_label.htmlFor = "pdf_toggle";
  pdfbtn_label.classList.add("btn", "btn-primary", "checking");
  pdfbtn_label.innerText = "transcript";
  pdfToggleDiv.appendChild(pdf_btn);
  pdfToggleDiv.appendChild(pdfbtn_label);
  pdf_t(src);
}

function pdf_t(pdf_src) {
  pdf_toggle.addEventListener("click", () => {
    if (pdf_toggle.checked) {
      pdf_btn = document.querySelector(".btn.checking");
      pdf_btn.classList.add("checked");
      const pdf_elem = document.createElement("embed");
      pdf_elem.src = pdf_src;
      // pdf_elem.classList.add("mx-auto");
      pdf_elem.id = "pdf_doc";
      pdf_elem.style.height = "97vh";
      pdf_elem.style.width = "47vw";
      pdf_parent.classList.add("col", "mx-auto");
      document.getElementById("pdf_parent").appendChild(pdf_elem);
    } else {
      pdf_btn = document.querySelector(".btn.checking");
      pdf_btn.classList.remove("checked");
      pdf_parent.classList.remove("col", "mx-auto");
      pdf_parent.innerHTML = ``;
    }
  });
}

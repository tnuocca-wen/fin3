function generate(ticker, year, qrtr, ser) {
  genbtn = document.getElementById("gen_btn");
  if (genbtn) {
    genbtn.addEventListener("click", (e) => {
      e.preventDefault();
      // circLoader();
      formdata = new FormData();
      console.log(ticker, year, qrtr);
      formdata.append("link", genbtn.href);
      formdata.append("ticker", ticker);
      formdata.append("year", year);
      formdata.append("quarter", qrtr);
      formdata.append("service", ser);
      console.log(formdata);
      fetch(gen_url, {
        method: "POST",
        body: formdata,
        headers: {
          "X-CSRFToken": csrf_token,
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok.");
          }
          const reader = response.body.getReader();
          pdfbtn_create(
            doc_root +
              "/" +
              ticker +
              "/" +
              year +
              "/" +
              qrtr +
              "/" +
              ticker +
              ".pdf"
          );
          fin_parent.innerHTML = ``;
          const fin_text = document.createElement("div");
          fin_text.id = "fin_text";
          fin_text.style.overflowY = "auto";
          fin_text.style.height = "97vh";
          fin_text.style.border = "1px dashed gray;";
          fin_text.style.whiteSpace = "pre-line";
          document.getElementById("fin_parent").appendChild(fin_text);
          const anchor = document.createElement("div");
          anchor.id = "anchor";
          fin_text.appendChild(anchor);
          // Function to consume the streaming data
          const processStream = ({ value, done }) => {
            if (done) {
              console.log("Streaming response complete.", done);
              if (response.status != 210) {
                upl_data(done, ticker, year, qrtr, ser);
                // sentiment_ret(ticker);
              }
              return;
            }
            // Assuming the streaming response is text data
            const chunk = new TextDecoder().decode(value);
            // chunk.replace("\n", "<br>");
            if (chunk.includes("<br><br>")) {
              txt1 = document.createTextNode(chunk.split("<br><br>")[0]);
              txt2 = document.createTextNode(chunk.split("<br><br>")[1]);
              for (var i = 0; i < 2; i++) {
                var brElement = document.createElement("br");
                brElement.appendChild(document.createTextNode("\n\n\n\n"));
                fin_text.insertBefore(brElement, anchor);
              }
              fin_text.insertBefore(txt2, anchor);
            } else {
              const newText = document.createTextNode(chunk);
              fin_text.insertBefore(newText, anchor);
            }
            // Continue reading the stream
            return reader.read().then(processStream);
          };

          // Start reading the stream
          if (response.status == 210) {
            reader.read().then(({ value, done }) => {
              msg = new TextDecoder().decode(value);
              const sm = document.createElement("div");
              sm.innerHTML = msg; //`<b>Generate</b> the <strong>SUMMARY FIRST</strong>`;
              fin_text.insertBefore(sm, anchor);
            });
          } else {
            return reader.read().then(processStream);
          }
        })
        .catch((error) => {
          console.error("There was a problem with the fetch operation:", error);
        });
    });
  }
}

function upl_data(done, ticker, year, qrtr, ser) {
  // console.log(JSON.stringify({"done": done, "tic": ticker, "yr": year, "qr": qrtr}));
  data = new FormData();
  data.append(
    "dat",
    JSON.stringify({ done: done, tic: ticker, yr: year, qr: qrtr, sr: ser })
  );
  fetch(upl_url, {
    method: "POST",
    body: data,
    headers: {
      "X-CSRFToken": csrf_token,
    },
  }).then((response) => {
    console.log(response);
    if (ser != 1) {
      sktdat();
      // strtktelab(5, -1);
    }
  });
}

var strtkteq = [];
function strtktelab(wq, id) {
  btar = [
    document.getElementById("q1gen"),
    document.getElementById("q2gen"),
    document.getElementById("q3gen"),
  ];
  console.log(btar);
  for (i = 0; i < btar.length; i++) {
    if (btar[i]) {
      if (wq == 1) {
        par1 = btar[0].parentElement;
        btar[0].remove();
        par1.innerHTML = `<div class="spinner-grow" style="border-radius: .5px;" role="status" style="margin-top: 2%;">
        <span class="visually-hidden">Loading...</span>
          </div>`;
        strtkteq.push(wq);
        break;
      } else if (wq == 2) {
        par2 = btar[1].parentElement;
        btar[1].remove();
        par2.innerHTML = `<div class="spinner-grow" style="border-radius: .5px;" role="status" style="margin-top: 2%;">
        <span class="visually-hidden">Loading...</span>
          </div>`;
        strtkteq.push(wq);
        break;
      } else if (wq == 3) {
        par3 = btar[2].parentElement;
        btar[2].remove();
        par3.innerHTML = `<div class="spinner-grow" style="border-radius: .5px;" role="status" style="margin-top: 2%;">
        <span class="visually-hidden">Loading...</span>
          </div>`;
        strtkteq.push(wq);
        break;
      }
    }
  }
  console.log(cur);

  data = new FormData();
  data.append("ticker", cur[0]);
  data.append("year", cur[1]);
  data.append("qrtr", cur[2]);
  data.append("wq", wq);
  console.log(id - 1);
  data.append("id", id - 1);

  // console.log(par);
  if (wq == 1){
  fetch(elab_url, {
    method: "POST",
    body: data,
    headers: {
      "X-CSRFToken": csrf_token,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok.");
      }
      if (par1){
      par1.innerHTML = ``;
      const reader = response.body.getReader();
      console.log("inside response of elab_url");
      // Function to consume the streaming data
      const processStream = ({ value, done }) => {
        if (done) {
          console.log("Streaming response complete.", done);
          // if (response.status != 210) {
          // }
          let tr = 0;
          for(let i=0;i<strtkteq.length; i++){
            if (strtkteq[i] == 1){
              tr = 1;
              break;
            }
          }
          if (tr == 1){
            strtkteq = strtkteq.filter(el => el != 1);
          }
          if (!strtkteq.length){
          sktdat();}
          return;
        }
        // Assuming the streaming response is text data
        const chunk = new TextDecoder().decode(value);
          par1.innerHTML += chunk; //(newText, anchor);
        // Continue reading the stream
        return reader.read().then(processStream);
      };
        return reader.read().then(processStream);
      // }
    }
    })
    .catch((error) => {
      console.error("There was a problem with the fetch operation:", error);
    });
  }
  else if (wq == 2){
    fetch(elab_url, {
      method: "POST",
      body: data,
      headers: {
        "X-CSRFToken": csrf_token,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok.");
        }
        if (par2){
        par2.innerHTML = ``;
        const reader = response.body.getReader();
        console.log("inside response of elab_url");
        // Function to consume the streaming data
        const processStream = ({ value, done }) => {
          if (done) {
            console.log("Streaming response complete.", done);
            // if (response.status != 210) {
            // }
            let tr = 0;
            for(let i=0;i<strtkteq.length; i++){
              if (strtkteq[i] == 2){
                tr = 1;
                break;
              }
            }
            if (tr == 1){
              strtkteq = strtkteq.filter(el => el != 2);
            }
            if (!strtkteq.length){
            sktdat();}
            return;
          }
          // Assuming the streaming response is text data
          const chunk = new TextDecoder().decode(value);
            par2.innerHTML += chunk; //(newText, anchor);
          // Continue reading the stream
          return reader.read().then(processStream);
        };
          return reader.read().then(processStream);
        // }
      }
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
      });
  }
  else if (wq == 3){
    fetch(elab_url, {
      method: "POST",
      body: data,
      headers: {
        "X-CSRFToken": csrf_token,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok.");
        }
        if (par3){
        par3.innerHTML = ``;
        const reader = response.body.getReader();
        console.log("inside response of elab_url");
        // Function to consume the streaming data
        const processStream = ({ value, done }) => {
          if (done) {
            console.log("Streaming response complete.", done);
            // if (response.status != 210) {
            // }
            let tr = 0;
            for(let i=0;i<strtkteq.length; i++){
              if (strtkteq[i] == 3){
                tr = 1;
                break;
              }
            }
            if (tr == 1){
              strtkteq = strtkteq.filter(el => el != 3);
            }
            if (!strtkteq.length){
            sktdat();}
            return;
          }
          // Assuming the streaming response is text data
          const chunk = new TextDecoder().decode(value);
            par3.innerHTML += chunk; //(newText, anchor);
          // Continue reading the stream
          return reader.read().then(processStream);
        };
          return reader.read().then(processStream);
        // }
      }
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
      });
  }
}

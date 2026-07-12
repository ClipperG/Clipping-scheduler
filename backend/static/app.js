// ==============================
// Clipping Scheduler Dashboard
// app.js - Part 1
// ==============================

const dropzone = document.getElementById("dropzone");
const input = document.getElementById("files");
const uploadBtn = document.getElementById("uploadBtn");

const progress = document.getElementById("progress");
const statusBox = document.getElementById("status");
const count = document.getElementById("count");
const fileList = document.getElementById("filelist");

let files = [];

// -------------------------------
// Click upload area
// -------------------------------

dropzone.addEventListener("click", () => {
    input.click();
});

// -------------------------------
// File picker
// -------------------------------

input.addEventListener("change", e => {

    files = [...e.target.files]
        .filter(f => f.name.toLowerCase().endsWith(".mp4"));

    updateList();

});

// -------------------------------
// Drag events
// -------------------------------

dropzone.addEventListener("dragover", e => {

    e.preventDefault();

    dropzone.classList.add("dragover");

});

dropzone.addEventListener("dragleave", () => {

    dropzone.classList.remove("dragover");

});

dropzone.addEventListener("drop", e => {

    e.preventDefault();

    dropzone.classList.remove("dragover");

    files = [...e.dataTransfer.files]
        .filter(f => f.name.toLowerCase().endsWith(".mp4"));

    updateList();

});

// -------------------------------
// Render selected files
// -------------------------------

function updateList(){

    count.innerText = `${files.length} video(s) selected`;

    fileList.innerHTML = "";

    files.forEach(file=>{

        const div = document.createElement("div");

        div.className = "file";

        div.innerHTML = `
            🎥 ${file.name}
            <span style="float:right;color:#94a3b8;">
                ${(file.size/1024/1024).toFixed(1)} MB
            </span>
        `;

        fileList.appendChild(div);

    });

}

// -------------------------------
// Upload button
// -------------------------------

uploadBtn.addEventListener("click", uploadAll);

// -------------------------------
// Upload videos
// -------------------------------

async function uploadAll(){

    if(files.length===0){

        alert("Please select some MP4 files.");

        return;

    }

    uploadBtn.disabled = true;

    progress.value = 0;

    statusBox.innerHTML = "Uploading...";

    const form = new FormData();

    files.forEach(file=>{

        form.append("files",file);

    });

    try{

        progress.value = 20;

        const response = await fetch("/upload",{

            method:"POST",

            body:form

        });

        progress.value = 80;

        const result = await response.json();

        if(!response.ok){

            throw new Error(result.detail || "Upload failed");

        }

        progress.value = 100;

        statusBox.innerHTML = `
            ✅ Uploaded ${result.uploaded} video(s)
        `;

        files = [];

        input.value = "";

        updateList();

        // Refresh dashboard after upload
        if(typeof loadDashboard === "function"){
            setTimeout(loadDashboard,1000);
        }

    }

    catch(err){

        console.error(err);

        progress.value = 0;

        statusBox.innerHTML = `
            ❌ ${err.message}
        `;

    }

    finally{

        uploadBtn.disabled = false;

    }

}
// ==========================================
// Clipping Scheduler Dashboard
// app.js - Part 2
// Dashboard + Queue + Stats
// ==========================================

const queueBody = document.getElementById("queueBody");
const searchBox = document.getElementById("search");
const refreshBtn = document.getElementById("refreshBtn");

let allVideos = [];

// -----------------------------
// Load Dashboard
// -----------------------------

async function loadDashboard(){

    try{

        const queueResponse = await fetch("/queue");
        const queue = await queueResponse.json();

        const scheduleResponse = await fetch("/schedule");
        const schedules = await scheduleResponse.json();

        allVideos = queue;

        renderStats(queue,schedules);
        renderQueue(queue,schedules);

    }

    catch(err){

        console.error(err);

    }

}

// -----------------------------
// Statistics
// -----------------------------

function renderStats(videos,schedules){

    let waiting = 0;
    let uploaded = 0;
    let scheduled = 0;
    let posted = 0;

    videos.forEach(video=>{

        switch(video.status){

            case "waiting":
                waiting++;
                break;

            case "uploaded":
                uploaded++;
                break;

            case "posted":
                posted++;
                break;

        }

    });

    schedules.forEach(schedule=>{

        if(schedule.status==="scheduled")
            scheduled++;

    });

    document.getElementById("waiting").innerText = waiting;
    document.getElementById("uploaded").innerText = uploaded;
    document.getElementById("scheduled").innerText = scheduled;
    document.getElementById("posted").innerText = posted;

}

// -----------------------------
// Queue Table
// -----------------------------

function renderQueue(videos,schedules){

    queueBody.innerHTML = "";

    let filter = "";

    if(searchBox)
        filter = searchBox.value.toLowerCase();

    videos
        .filter(v=>v.filename.toLowerCase().includes(filter))
        .forEach(video=>{

            const schedule = schedules.find(s=>s.video_id===video.id);

            const tr = document.createElement("tr");

            tr.innerHTML = `

<td>${video.id}</td>

<td>${video.filename}</td>

<td>
<span class="badge ${video.status}">
${video.status}
</span>
</td>

<td>
${schedule ? schedule.scheduled_time : "-"}
</td>

<td>

<button
class="action-btn post-btn"
onclick="postNow(${video.id})">

🚀 Post

</button>

<button
class="action-btn edit-btn"
onclick="editSchedule(${video.id})">

📅 Edit

</button>

<button
class="action-btn delete-btn"
onclick="deleteVideo(${video.id})">

🗑 Delete

</button>

</td>

`;

            queueBody.appendChild(tr);

        });

}

// -----------------------------
// Search
// -----------------------------

if(searchBox){

    searchBox.addEventListener("keyup",()=>{

        loadDashboard();

    });

}

// -----------------------------
// Manual Refresh
// -----------------------------

if(refreshBtn){

    refreshBtn.addEventListener("click",()=>{

        loadDashboard();

    });

}

// -----------------------------
// Auto Refresh
// -----------------------------

setInterval(loadDashboard,5000);

// -----------------------------
// First Load
// -----------------------------

loadDashboard();
loadBufferAccounts();
// ==========================================
// app.js - Part 3
// Actions
// ==========================================

// -----------------------------
// Delete Video
// -----------------------------
async function deleteVideo(id){

    if(!confirm("Delete this video?"))
        return;

    try{

        const response = await fetch(`/queue/${id}`,{
            method:"DELETE"
        });

        if(!response.ok)
            throw new Error("Delete failed");

        statusBox.innerHTML = "🗑 Video deleted";

        loadDashboard();

    }

    catch(err){

        console.error(err);

        alert(err.message);

    }

}

// -----------------------------
// Post Immediately
// -----------------------------
async function postNow(id){

    if(!confirm("Post this video now?"))
        return;

    try{

        const response = await fetch(`/queue/${id}/post`,{
            method:"POST"
        });

        const result = await response.json();

        if(!response.ok)
            throw new Error(result.detail || "Unable to post");

        statusBox.innerHTML = "🚀 Video queued for Buffer";

        loadDashboard();

    }

    catch(err){

        console.error(err);

        alert(err.message);

    }

}

// -----------------------------
// Edit Schedule
// -----------------------------
async function editSchedule(id) {
    const input = document.createElement("input");

    input.type = "datetime-local";
    input.style.position = "fixed";
    input.style.left = "50%";
    input.style.top = "50%";
    input.style.transform = "translate(-50%, -50%)";
    input.style.padding = "10px";
    input.style.fontSize = "16px";
    input.style.zIndex = "9999";

    document.body.appendChild(input);

    input.focus();
    input.showPicker?.();

    input.onchange = async () => {
        const value = input.value;

        document.body.removeChild(input);

        if (!value) return;

        try {
            const response = await fetch(`/schedule/${id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    scheduled_time: value.replace("T", " ")
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to update");
            }

            statusBox.innerHTML = "✅ Schedule updated";

            loadDashboard();

        } catch (err) {
            console.error(err);
            alert(err.message);
        }
    };
}

// -----------------------------
// Clear Queue
// -----------------------------
const clearBtn = document.getElementById("clearBtn");

if(clearBtn){

    clearBtn.addEventListener("click", async ()=>{

        if(!confirm(
            "Delete ALL videos and schedules?"
        ))
            return;

        try{

            const response = await fetch("/queue",{

                method:"DELETE"

            });

            if(!response.ok)
                throw new Error("Unable to clear queue");

            statusBox.innerHTML =
                "🧹 Queue cleared";

            loadDashboard();

        }

        catch(err){

            console.error(err);

            alert(err.message);

        }

    });

}
// ==============================
// BUFFER ACCOUNTS
// ==============================

async function loadBufferAccounts() {
    const res = await fetch("/buffer-accounts/");
    const accounts = await res.json();

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Active</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    accounts.forEach(account => {
        html += `
            <tr>
                <td>${account.name}</td>
                <td>${account.active ? "✅" : "❌"}</td>
                <td>
    <button onclick="activateBufferAccount(${account.id})">
        Use
    </button>

    <button onclick="deleteBufferAccount(${account.id})">
        Delete
    </button>
</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    document.getElementById("bufferAccounts").innerHTML = html;
}

async function addBufferAccount() {

    const name = document.getElementById("bufferName").value;
    const token = document.getElementById("bufferToken").value;

    if (!name || !token) {
        alert("Fill in both fields.");
        return;
    }

    const response = await fetch("/buffer-accounts/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            api_token: token
        })
    });

    if (!response.ok) {
        const error = await response.text();
        alert(error);
        return;
    }

    document.getElementById("bufferName").value = "";
    document.getElementById("bufferToken").value = "";

    loadBufferAccounts();
}

async function deleteBufferAccount(id) {

    await fetch(`/buffer-accounts/${id}`, {
        method: "DELETE"
    });

    loadBufferAccounts();
}

// Initial page load
loadDashboard();
loadBufferAccounts();
async function activateBufferAccount(id) {

    await fetch(`/buffer-accounts/${id}/activate`, {
        method: "PUT"
    });

    loadBufferAccounts();
}
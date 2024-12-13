import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

function App() {
  const [soilMoisture, setSoilMoisture] = useState("");
  const [responseMessage, setResponseMessage] = useState("");
  const [command, setCommand] = useState("");
  const [logs, setLogs] = useState([]);

  const fetchCommand = async () => {
    const response = await fetch("/command");
    const data = await response.json();
    setCommand(data.command);
  };

  const sendCommand = async (newCommand) => {
    await fetch("/update-command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: newCommand }),
    });
    setCommand(newCommand);
  };

  const sendSoilData = async (event) => {
    event.preventDefault();
    const response = await fetch("/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ soil_moisture: soilMoisture }),
    });
    const data = await response.json();
    setResponseMessage(data.message);
  };

  const fetchLogs = async () => {
    const response = await fetch("/logs");
    const data = await response.json();

    const cleanedData = data
      .filter((entry) => entry.soil_moisture !== null)
      .map((entry) => ({
        ...entry,
        soil_moisture: Number(entry.soil_moisture),
      }));
    console.log(cleanedData);
    setLogs(cleanedData);
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const chartData = {
    labels: logs.map((entry) => entry.timestamp),
    datasets: [
      {
        label: "Soil Moisture Level",
        data: logs.map((entry) => entry.soil_moisture),
        fill: false,
        borderColor: "blue",
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Soil Moisture Over Time",
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Timestamp",
        },
        ticks: {
          callback: function (value, index, ticks) {
            const timestamp = logs[index]?.timestamp;
            return timestamp ? timestamp.split(" ")[1] : "";
          },
          maxRotation: 45,
          minRotation: 45,
        },
      },
      y: {
        title: {
          display: true,
          text: "Moisture Level",
        },
        beginAtZero: true,
      },
    },
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Soil Monitoring System</h1>
      <h2>Current Command: {command}</h2>
      <button onClick={fetchCommand}>Fetch Command</button>
      <br />
      <br />
      <button onClick={() => sendCommand("Move Motor")}>
        Send "Move Motor"
      </button>
      <button onClick={() => sendCommand("Stop Motor")}>
        Send "Stop Motor"
      </button>
      <button onClick={() => sendCommand("Play Sound")}>
        Send "Play Sound"
      </button>
      <button onClick={() => sendCommand("Stop Sound")}>
        Send "Stop Sound"
      </button>
      <button onClick={() => sendCommand("Start Water")}>
        Send "Start Water"
      </button>
      <button onClick={() => sendCommand("Stop Water")}>
        Send "Stop Water"
      </button>
      <br />
      <br />
      <h2>Send Soil Moisture Data</h2>
      <form onSubmit={sendSoilData}>
        <label>
          Soil Moisture:
          <input
            type="number"
            value={soilMoisture}
            onChange={(e) => setSoilMoisture(e.target.value)}
            placeholder="Enter soil moisture"
            required
          />
        </label>
        <button type="submit">Send Data</button>
      </form>
      <p>Response: {responseMessage}</p>

      <br />
      <br />
      <h2>Soil Moisture Over Time</h2>
      <button onClick={fetchLogs}>Refresh Logs</button>
      <div style={{ maxWidth: "800px", margin: "auto" }}>
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
}

export default App;

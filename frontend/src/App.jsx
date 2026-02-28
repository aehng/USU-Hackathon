import Dashboard from "./Dashboard.jsx";
import { RefreshProvider } from "./context/RefreshContext.jsx";

function App() {
  return (
    <RefreshProvider>
      <Dashboard />
    </RefreshProvider>
  );
}

export default App

import { useState, useEffect } from "react";
import { getHistory, updateEntry } from "../api/client.js";

export default function LogHistory() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getHistory();
      if (data.entries) setEntries(data.entries);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (entry) => {
    setEditingId(entry.id);
    setEditForm({
      symptoms: entry.symptoms?.join(", ") || "",
      potential_triggers: entry.potential_triggers?.join(", ") || "",
      severity: entry.severity || "",
      notes: entry.notes || ""
    });
  };

  const handleSave = async (id) => {
    try {
      // Convert comma-separated strings back to arrays
      const payload = {
        symptoms: editForm.symptoms.split(",").map(s => s.trim()).filter(s => s),
        potential_triggers: editForm.potential_triggers.split(",").map(s => s.trim()).filter(s => s),
        severity: editForm.severity ? parseInt(editForm.severity) : null,
        notes: editForm.notes
      };

      await updateEntry(id, payload);
      setEditingId(null);
      fetchLogs(); // Refresh the list
    } catch (error) {
      console.error("Failed to update entry:", error);
      alert("Failed to save changes.");
    }
  };

  if (loading) return <p className="text-sm text-slate-500">Loading history...</p>;
  if (entries.length === 0) return <p className="text-sm text-slate-500">No logs found.</p>;

  return (
    <div className="space-y-4">
      {entries.map((entry) => (
        <div key={entry.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-slate-500">
              {new Date(entry.logged_at).toLocaleString()}
            </span>
            {editingId !== entry.id ? (
              <button 
                onClick={() => handleEditClick(entry)}
                className="text-xs font-medium text-orange-600 hover:text-orange-800"
              >
                Edit
              </button>
            ) : (
              <div className="space-x-2">
                <button 
                  onClick={() => handleSave(entry.id)}
                  className="text-xs font-medium text-green-600 hover:text-green-800"
                >
                  Save
                </button>
                <button 
                  onClick={() => setEditingId(null)}
                  className="text-xs font-medium text-slate-500 hover:text-slate-700"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {editingId === entry.id ? (
            <div className="space-y-3 mt-3">
              <div>
                <label className="block text-xs font-medium text-slate-700">Severity (1-10)</label>
                <input 
                  type="number" 
                  min="1" max="10"
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={editForm.severity}
                  onChange={(e) => setEditForm({...editForm, severity: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700">Symptoms (comma separated)</label>
                <input 
                  type="text" 
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={editForm.symptoms}
                  onChange={(e) => setEditForm({...editForm, symptoms: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700">Triggers (comma separated)</label>
                <input 
                  type="text" 
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={editForm.potential_triggers}
                  onChange={(e) => setEditForm({...editForm, potential_triggers: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700">Notes</label>
                <textarea 
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={editForm.notes}
                  onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
                />
              </div>
            </div>
          ) : (
            <div>
              <p className="text-sm font-medium text-slate-900 mb-1">
                Severity: {entry.severity ? `${entry.severity}/10` : 'N/A'}
              </p>
              <p className="text-sm text-slate-700 mb-1">
                <span className="font-semibold">Symptoms:</span> {entry.symptoms?.join(', ') || 'None'}
              </p>
              <p className="text-sm text-slate-700 mb-1">
                <span className="font-semibold">Triggers:</span> {entry.potential_triggers?.join(', ') || 'None'}
              </p>
              {entry.notes && (
                <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-2 rounded">
                  {entry.notes}
                </p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
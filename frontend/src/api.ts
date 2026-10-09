import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('workspace_token');
  if (token) {
    config.headers['x-workspace-token'] = token;
  }
  return config;
});

export const initializeWorkspace = async () => {
  const res = await api.post('/workspaces/');
  localStorage.setItem('workspace_token', res.data.token);
  return res.data;
};

export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/uploads/', formData);
  return res.data;
};

export const listDatasets = async () => {
  const res = await api.get('/datasets/');
  return res.data;
};

export const createScenario = async (datasetId: string, name: string, configJson: any) => {
  const res = await api.post('/scenarios/', {
    dataset_id: datasetId,
    name,
    config_json: configJson
  });
  return res.data;
};

export const startRun = async (scenarioId: string) => {
  const res = await api.post('/runs/', {
    scenario_id: scenarioId
  });
  return res.data;
};

export const getRun = async (runId: string) => {
  const res = await api.get(`/runs/${runId}`);
  return res.data;
};

export const downloadReport = async (runId: string) => {
  const res = await api.get(`/runs/${runId}/report/download`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `report_${runId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
};


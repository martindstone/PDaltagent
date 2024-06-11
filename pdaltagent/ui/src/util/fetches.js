import {
  urlFor,
} from './helpers';

const addMaint = async (data) => {
  const csrfToken = sessionStorage.getItem('csrfToken');
  const response = await fetch(urlFor('/maints'), {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-TOKEN': csrfToken,
      },
      body: JSON.stringify(data)
  });
  return await response.json();
};

const updateMaint = async (id, data) => {
  const csrfToken = sessionStorage.getItem('csrfToken');
  const response = await fetch(urlFor(`/maints/${id}`), {
      method: 'PUT',
      headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-TOKEN': csrfToken,
      },
      body: JSON.stringify(data)
  });
  return await response.json();
};

export {
  addMaint,
  updateMaint,
};
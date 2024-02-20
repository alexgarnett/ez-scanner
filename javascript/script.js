const constraints = {
  video: {
    width: {
      ideal: 1080,
    },
    height: {
      ideal: 720,
    },
  }
};

const startStream = async (constraints) => {
  const stream = await navigator.mediaDevices.getUserMedia(constraints);
  handleStream(stream);
};

startStream(constraints);


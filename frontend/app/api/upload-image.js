import AWS from 'aws-sdk';

const s3 = new AWS.S3();

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { file } = req.body;

    // Generate a unique name for the image file in S3
    const imgKey = `dfu-images/${Date.now()}-${file.name}`;

    const params = {
      Bucket: process.env.BUCKET_NAME,   // Make sure to set BUCKET_NAME in .env.local
      Key: imgKey,
      Body: Buffer.from(file.data, 'base64'),
      ContentType: 'image/jpeg',
    };

    try {
      const s3Response = await s3.upload(params).promise();
      res.status(200).json({ img_key: s3Response.Key });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: 'Failed to upload image' });
    }
  } else {
    res.status(405).json({ error: 'Method Not Allowed' });
  }
}
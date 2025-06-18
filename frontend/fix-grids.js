const fs = require('fs');
const path = require('path');

function replaceGridsInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace Grid container with Box
  content = content.replace(
    /<Grid container spacing={3}>/g,
    '<Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", md: "1fr 1fr 1fr" }, gap: 3 }}>'
  );
  
  // Replace Grid container with different spacing
  content = content.replace(
    /<Grid container spacing={2}>/g,
    '<Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 2 }}>'
  );
  
  // Replace Grid container alignItems
  content = content.replace(
    /<Grid container spacing={3} alignItems="center">/g,
    '<Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", md: "1fr 1fr 1fr" }, gap: 3, alignItems: "center" }}>'
  );
  
  // Replace Grid items with Box
  content = content.replace(
    /<Grid item xs={12}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid item xs={12} sm={6} md={4}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid item xs={12} md={6} lg={4}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid item xs={12} md={6}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid xs={12} sm={6} md={4}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid xs={12} md={6} lg={4}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid xs={12}>/g,
    '<Box>'
  );
  
  content = content.replace(
    /<Grid xs={6}>/g,
    '<Box>'
  );
  
  // Close Grid tags
  content = content.replace(
    /<\/Grid>/g,
    '</Box>'
  );
  
  fs.writeFileSync(filePath, content);
}

// Process all tsx files
const srcDir = './src';
function processDirectory(dir) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      processDirectory(filePath);
    } else if (file.endsWith('.tsx')) {
      console.log('Processing:', filePath);
      replaceGridsInFile(filePath);
    }
  });
}

processDirectory(srcDir);
console.log('Grid replacement complete!');
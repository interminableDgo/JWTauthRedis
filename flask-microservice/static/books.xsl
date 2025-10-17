<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" doctype-system="about:legacy-compat" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <html>
    <head>
      <title>Catálogo de Libros (XML)</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
      </style>
    </head>
    <body>
      <h1>Catálogo de Libros</h1>
      <table>
        <thead>
          <tr>
            <th>ISBN</th>
            <th>Título</th>
            <th>Autor</th>
            <th>Año</th>
            <th>Género</th>
          </tr>
        </thead>
        <tbody>
          <xsl:for-each select="books/book">
            <tr>
              <td><xsl:value-of select="isbn"/></td>
              <td><xsl:value-of select="title"/></td>
              <td><xsl:value-of select="author_name"/></td>
              <td><xsl:value-of select="year"/></td>
              <td><xsl:value-of select="genre_name"/></td>
            </tr>
          </xsl:for-each>
        </tbody>
      </table>
    </body>
  </html>
</xsl:template>
</xsl:stylesheet>
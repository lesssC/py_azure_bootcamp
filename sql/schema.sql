-- chambaYA: esquema para Azure SQL Database.
-- Ejecutar una vez sobre la base de datos sqldb-redsosten.

CREATE TABLE Beneficiarios (
    BeneficiarioID INT IDENTITY(1,1) PRIMARY KEY,
    NombreCompleto VARCHAR(100) NOT NULL,
    TelefonoContacto VARCHAR(20) NOT NULL,
    ZonaComunitaria VARCHAR(100) NOT NULL,
    FechaRegistro DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE HabilidadesEmpiricas (
    HabilidadID INT IDENTITY(1,1) PRIMARY KEY,
    BeneficiarioID INT NOT NULL,
    Categoria VARCHAR(50) NOT NULL,
    DescripcionExperiencia VARCHAR(MAX) NULL,
    CONSTRAINT FK_Habilidades_Beneficiarios
        FOREIGN KEY (BeneficiarioID) REFERENCES Beneficiarios(BeneficiarioID)
);
GO

CREATE TABLE OfertasOportunidades (
    OfertaID INT IDENTITY(1,1) PRIMARY KEY,
    TituloVacante VARCHAR(100) NOT NULL,
    Fuente VARCHAR(50) NOT NULL,
    DireccionUbicacion VARCHAR(150) NOT NULL,
    TelefonoContacto VARCHAR(20) NOT NULL,
    RequisitosMinimos VARCHAR(MAX) NULL,
    FechaRegistro DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    Activo BIT NOT NULL DEFAULT 1
);
GO

CREATE INDEX IX_Ofertas_Activas ON OfertasOportunidades (Activo, Fuente);
GO

INSERT INTO OfertasOportunidades
    (TituloVacante, Fuente, DireccionUbicacion, TelefonoContacto, RequisitosMinimos)
VALUES
    ('Ayudante de Pintura y Drywall', 'Bodega_Mercado', 'Av. Las Flores 450, Mz B Lote 3', '987654321', 'Experiencia práctica en brocha o empaste. Ganas de trabajar.'),
    ('Asistente de Cocina y Menú', 'Pyme_Local', 'Mercado Central, Puesto 12', '912345678', 'Saber picar verduras y limpiar. Horario de mañanas.'),
    ('Taller Práctico de Electricidad Residencial', 'CETPRO', 'Parroquia San José, Salón Comunal', '955554433', 'Sin experiencia. Taller gratuito de dos semanas.');
GO
